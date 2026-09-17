import mimetypes
import os
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from hub.models import MediaAlbum, MediaAsset, UserProfile


ALBUM_NAME = "Oko and Atteh Picture Archive"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class Command(BaseCommand):
    help = "Import the optimized picture archive into persistent Django media storage."

    def handle(self, *args, **options):
        source_root = Path(os.environ.get("PICTURE_ARCHIVE_SOURCE", "/app/seed-pictures"))
        if not source_root.is_dir():
            self.stdout.write(self.style.WARNING(f"Picture archive source not found: {source_root}"))
            return

        album, _ = MediaAlbum.objects.get_or_create(
            name=ALBUM_NAME,
            defaults={
                "description": "The complete optimized family and memorial picture archive.",
                "created_by_name": "Funeral Administrator",
                "created_by_role": UserProfile.Role.ADMIN,
                "available_to_media": True,
            },
        )
        imported = 0
        repaired = 0
        for source_path in sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS):
            relative_path = source_path.relative_to(source_root).as_posix()
            seed_marker = f"archive-source:{relative_path}"
            legacy_url = f"/web-pictures/{relative_path}"
            item = album.assets.filter(notes=seed_marker).first() or album.assets.filter(external_url=legacy_url).first()
            if item and item.file and item.file.storage.exists(item.file.name):
                continue
            if not item:
                item = MediaAsset(album=album)
                imported += 1
            else:
                repaired += 1
            mime_type = mimetypes.guess_type(source_path.name)[0] or "image/jpeg"
            item.title = source_path.stem
            item.asset_type = MediaAsset.AssetType.MEDIA
            item.category = "Photo Albums"
            item.description = "Picture from the Oko and Atteh memorial archive."
            item.external_url = ""
            item.original_name = source_path.name
            item.mime_type = mime_type
            item.size_bytes = source_path.stat().st_size
            item.labels = ["picture archive"]
            item.uploaded_by_name = "Funeral Administrator"
            item.confidentiality = "Internal"
            item.document_status = MediaAsset.Status.APPROVED
            item.available_to_media = True
            item.notes = seed_marker
            with source_path.open("rb") as source_file:
                item.file.save(source_path.name, File(source_file), save=False)
                item.save()

        self.stdout.write(self.style.SUCCESS(
            f"Picture album ready: {album.assets.count()} files ({imported} imported, {repaired} migrated or repaired)."
        ))
