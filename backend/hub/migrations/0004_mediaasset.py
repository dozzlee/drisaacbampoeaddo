import uuid
from django.db import migrations, models


def seed_existing_assets(apps, schema_editor):
    MediaAsset = apps.get_model("hub", "MediaAsset")
    records = [
        ("Official memorial portrait", "media", "Official Photographs", "Approved memorial portrait.", "/web-pictures/headerfinal.png", "headerfinal.png", "image/png", True),
        ("Official logo", "media", "Website Content", "Approved identity mark.", "/logo/logo_new.png", "logo_new.png", "image/png", True),
        ("One Week Remembrance booklet", "document", "Remembrance Service", "One week remembrance service booklet.", "/booklet-assets/one-week-remembrance-service.pdf", "one-week-remembrance-service.pdf", "application/pdf", True),
        ("Order of Service", "document", "Order of Service", "Order of service document.", "/booklet-assets/order-of-service.jpg", "order-of-service.jpg", "image/jpeg", False),
        ("Hymns", "document", "Brochure Content", "Hymns prepared for the service.", "/booklet-assets/hymns.jpg", "hymns.jpg", "image/jpeg", False),
        ("Legacy photograph 01", "media", "Media Archive", "Legacy photograph.", "/web-pictures/F18_5598.JPG", "F18_5598.JPG", "image/jpeg", True),
        ("Legacy photograph 02", "media", "Media Archive", "Legacy photograph.", "/web-pictures/F18_9952.JPG", "F18_9952.JPG", "image/jpeg", True),
    ]
    for title, asset_type, category, description, url, name, mime, shared in records:
        MediaAsset.objects.get_or_create(
            title=title,
            defaults={"asset_type": asset_type, "category": category, "description": description, "external_url": url, "original_name": name, "mime_type": mime, "available_to_media": shared, "document_status": "approved", "uploaded_by_name": "System migration"},
        )


class Migration(migrations.Migration):
    dependencies = [("hub", "0003_reset_tribute_party_sequence")]
    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("asset_type", models.CharField(choices=[("media", "Media"), ("document", "Document")], max_length=12)),
                ("category", models.CharField(max_length=160)),
                ("description", models.TextField()),
                ("file", models.FileField(blank=True, upload_to="library/%Y/%m/")),
                ("external_url", models.CharField(blank=True, max_length=500)),
                ("original_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(max_length=160)),
                ("size_bytes", models.PositiveBigIntegerField(default=0)),
                ("labels", models.JSONField(blank=True, default=list)),
                ("date_created", models.DateField(blank=True, null=True)),
                ("event_activity", models.CharField(blank=True, max_length=160)),
                ("responsible_committee", models.CharField(blank=True, max_length=160)),
                ("uploaded_by_name", models.CharField(blank=True, max_length=160)),
                ("owner_contact", models.CharField(blank=True, max_length=160)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("confidentiality", models.CharField(default="Internal", max_length=80)),
                ("version", models.CharField(default="1.0", max_length=40)),
                ("document_status", models.CharField(choices=[("draft", "Draft"), ("review", "Under review"), ("approved", "Approved"), ("archived", "Archived")], default="draft", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("available_to_media", models.BooleanField(default=False)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.RunPython(seed_existing_assets, migrations.RunPython.noop),
    ]
