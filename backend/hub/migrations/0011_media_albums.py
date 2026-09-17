import uuid
from pathlib import PurePosixPath

from django.db import migrations, models
import django.db.models.deletion


def seed_picture_archive(apps, schema_editor):
    from hub.picture_archive import PICTURE_ARCHIVE

    MediaAlbum = apps.get_model("hub", "MediaAlbum")
    MediaAsset = apps.get_model("hub", "MediaAsset")
    album, _ = MediaAlbum.objects.get_or_create(
        name="Oko and Atteh Picture Archive",
        defaults={
            "description": "The complete optimized family and memorial picture archive.",
            "created_by_name": "Funeral Administrator",
            "created_by_role": "admin",
            "available_to_media": True,
        },
    )
    existing = set(album.assets.values_list("external_url", flat=True))
    records = []
    for relative_path, size_bytes in PICTURE_ARCHIVE:
        url = f"/web-pictures/{relative_path}"
        if url in existing:
            continue
        name = PurePosixPath(relative_path).name
        extension = PurePosixPath(name).suffix.lower()
        mime_type = "image/png" if extension == ".png" else "image/gif" if extension == ".gif" else "image/jpeg"
        records.append(MediaAsset(
            album=album, title=PurePosixPath(name).stem, asset_type="media",
            category="Photo Albums", description="Picture from the Oko and Atteh memorial archive.",
            external_url=url, original_name=name, mime_type=mime_type, size_bytes=size_bytes,
            labels=["picture archive"], uploaded_by_name="Funeral Administrator",
            confidentiality="Internal", document_status="approved", available_to_media=True,
        ))
    MediaAsset.objects.bulk_create(records, batch_size=200)


class Migration(migrations.Migration):
    dependencies = [("hub", "0010_tag_oko_tributes")]
    operations = [
        migrations.CreateModel(
            name="MediaAlbum",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("created_by_name", models.CharField(blank=True, max_length=160)),
                ("created_by_role", models.CharField(choices=[("admin", "Admin"), ("user", "Normal user"), ("media", "Media person")], default="user", max_length=10)),
                ("available_to_media", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddField(
            model_name="mediaasset", name="album",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assets", to="hub.mediaalbum"),
        ),
        migrations.RunPython(seed_picture_archive, migrations.RunPython.noop),
    ]
