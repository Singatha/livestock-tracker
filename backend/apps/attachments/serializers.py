from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from apps.animals.models import Animal

from .models import Attachment
from .validation import validate_attachment_content


class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "animal",
            "category",
            "title",
            "description",
            "file",
            "original_filename",
            "content_type",
            "size_bytes",
            "uploaded_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "content_type",
            "size_bytes",
            "uploaded_by_name",
            "created_at",
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.email or obj.uploaded_by.username

    def validate_animal(self, animal: Animal | None):
        if animal and animal.farm_id != self.context["farm"].id:
            raise serializers.ValidationError("Animal does not belong to the selected farm")
        return animal

    def validate_file(self, upload):
        if upload.size > settings.ATTACHMENT_MAX_SIZE:
            maximum = settings.ATTACHMENT_MAX_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f"File must not exceed {maximum} MB")
        validate_attachment_content(upload)
        return upload

    def create(self, validated_data):
        upload = validated_data["file"]
        farm = validated_data.pop("farm", self.context["farm"])
        return Attachment.objects.create(
            **validated_data,
            farm=farm,
            uploaded_by=self.context["request"].user,
            original_filename=Path(upload.name).name,
            content_type=(upload.content_type or "application/octet-stream").lower(),
            size_bytes=upload.size,
        )
