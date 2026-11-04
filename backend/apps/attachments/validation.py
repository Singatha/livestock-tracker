from pathlib import Path
from zipfile import BadZipFile, ZipFile

from rest_framework import serializers

CONTENT_TYPES_BY_EXTENSION = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".csv": {"text/csv"},
}


def validate_attachment_content(upload) -> None:
    extension = Path(upload.name).suffix.lower()
    content_type = (upload.content_type or "").lower()
    allowed_content_types = CONTENT_TYPES_BY_EXTENSION.get(extension)
    if allowed_content_types is None:
        raise serializers.ValidationError("Unsupported file extension")
    if content_type not in allowed_content_types:
        raise serializers.ValidationError("File extension and content type do not match")

    position = upload.tell()
    try:
        upload.seek(0)
        header = upload.read(16)
        if extension in {".jpg", ".jpeg"}:
            valid = header.startswith(b"\xff\xd8\xff")
        elif extension == ".png":
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        elif extension == ".webp":
            valid = header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        elif extension == ".pdf":
            valid = header.startswith(b"%PDF-")
        elif extension == ".doc":
            valid = header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        elif extension == ".docx":
            valid = _is_word_document(upload)
        else:
            valid = _is_utf8_csv(upload)
    finally:
        upload.seek(position)

    if not valid:
        raise serializers.ValidationError("File content does not match its declared type")


def _is_word_document(upload) -> bool:
    upload.seek(0)
    try:
        with ZipFile(upload) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and any(
                name.startswith("word/") for name in names
            )
    except (BadZipFile, OSError):
        return False


def _is_utf8_csv(upload) -> bool:
    upload.seek(0)
    content = upload.read()
    if b"\x00" in content:
        return False
    try:
        content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return False
    return True
