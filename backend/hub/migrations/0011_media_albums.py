import uuid

from django.db import migrations, models
import django.db.models.deletion


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
    ]
