from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient

from apps.animals.models import Animal
from apps.attachments.models import Attachment
from apps.farms.models import Farm, FarmMembership

pytestmark = pytest.mark.django_db


def farm_headers(farm):
    return {"HTTP_X_FARM_ID": str(farm.id)}


def image_upload(name="sheep.jpg", content=b"\xff\xd8\xff test image"):
    return SimpleUploadedFile(name, content, content_type="image/jpeg")


@override_settings(MEDIA_ROOT=None)
def test_worker_can_upload_and_download_animal_attachment(
    api_client, farm, user, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    animal = Animal.objects.create(farm=farm, ear_tag="DOC-1", species="sheep")

    response = api_client.post(
        "/api/v1/attachments/",
        {
            "animal": str(animal.id),
            "category": "photo",
            "title": "Side profile",
            "file": image_upload(),
        },
        format="multipart",
        **farm_headers(farm),
    )

    assert response.status_code == 201
    attachment = Attachment.objects.get(id=response.data["id"])
    assert attachment.uploaded_by == user
    assert attachment.file.name.startswith(f"attachments/{farm.id}/")
    assert Path(attachment.file.path).exists()

    download = api_client.get(f"/api/v1/attachments/{attachment.id}/content/", **farm_headers(farm))
    assert download.status_code == 200
    assert download["Content-Type"] == "image/jpeg"
    assert download["X-Content-Type-Options"] == "nosniff"
    assert b"".join(download.streaming_content) == b"\xff\xd8\xff test image"


def test_attachment_list_and_content_are_farm_scoped(api_client, farm, user, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    other_farm = Farm.objects.create(name="Other", owner=user)
    FarmMembership.objects.create(farm=other_farm, user=user, role=FarmMembership.Role.OWNER)
    attachment = Attachment.objects.create(
        farm=other_farm,
        category="certificate",
        title="Private certificate",
        file=image_upload(),
        original_filename="certificate.jpg",
        content_type="image/jpeg",
        size_bytes=10,
        uploaded_by=user,
    )

    listing = api_client.get("/api/v1/attachments/", **farm_headers(farm))
    content = api_client.get(f"/api/v1/attachments/{attachment.id}/content/", **farm_headers(farm))

    assert listing.status_code == 200
    assert listing.data["count"] == 0
    assert content.status_code == 404


def test_upload_rejects_unsupported_and_oversized_files(api_client, farm, settings):
    unsupported = api_client.post(
        "/api/v1/attachments/",
        {
            "category": "other",
            "title": "Executable",
            "file": SimpleUploadedFile(
                "unsafe.exe", b"binary", content_type="application/x-msdownload"
            ),
        },
        format="multipart",
        **farm_headers(farm),
    )
    settings.ATTACHMENT_MAX_SIZE = 3
    oversized = api_client.post(
        "/api/v1/attachments/",
        {"category": "photo", "title": "Large", "file": image_upload(content=b"1234")},
        format="multipart",
        **farm_headers(farm),
    )

    assert unsupported.status_code == 400
    assert "file" in unsupported.data
    assert oversized.status_code == 400
    assert "file" in oversized.data


def test_upload_rejects_spoofed_file_content(api_client, farm):
    spoofed_image = api_client.post(
        "/api/v1/attachments/",
        {
            "category": "photo",
            "title": "Spoofed image",
            "file": SimpleUploadedFile(
                "sheep.jpg", b"%PDF-1.7 fake image", content_type="image/jpeg"
            ),
        },
        format="multipart",
        **farm_headers(farm),
    )
    mismatched_type = api_client.post(
        "/api/v1/attachments/",
        {
            "category": "certificate",
            "title": "Mismatched document",
            "file": SimpleUploadedFile(
                "certificate.pdf", b"%PDF-1.7 valid header", content_type="image/jpeg"
            ),
        },
        format="multipart",
        **farm_headers(farm),
    )

    assert spoofed_image.status_code == 400
    assert "content does not match" in str(spoofed_image.data["file"][0])
    assert mismatched_type.status_code == 400
    assert "extension and content type" in str(mismatched_type.data["file"][0])


def test_uploader_can_delete_file_and_metadata(api_client, farm, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    uploaded = api_client.post(
        "/api/v1/attachments/",
        {"category": "invoice", "title": "Vet invoice", "file": image_upload()},
        format="multipart",
        **farm_headers(farm),
    )
    attachment = Attachment.objects.get(id=uploaded.data["id"])
    stored_path = Path(attachment.file.path)

    response = api_client.delete(f"/api/v1/attachments/{attachment.id}/", **farm_headers(farm))

    assert response.status_code == 204
    assert not Attachment.objects.filter(id=attachment.id).exists()
    assert not stored_path.exists()


def test_viewer_cannot_upload_attachment(farm, other_user):
    FarmMembership.objects.create(farm=farm, user=other_user, role=FarmMembership.Role.VIEWER)
    client = APIClient()
    client.force_login(other_user)

    response = client.post(
        "/api/v1/attachments/",
        {"category": "photo", "title": "Attempt", "file": image_upload()},
        format="multipart",
        **farm_headers(farm),
    )

    assert response.status_code == 403
