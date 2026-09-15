import django.db.models.deletion
import uuid
from django.db import migrations, models
class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="UserProfile", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("full_name", models.CharField(max_length=160)), ("phone", models.CharField(max_length=32)), ("normalized_phone", models.CharField(editable=False, max_length=15, unique=True)), ("role", models.CharField(choices=[("admin", "Admin"), ("user", "Normal user"), ("media", "Media person")], max_length=10)), ("created_at", models.DateTimeField(auto_now_add=True))]),
        migrations.CreateModel(name="TributeAttachment", fields=[("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("party_id", models.PositiveBigIntegerField(db_index=True)), ("file", models.FileField(upload_to="tributes/%Y/%m/")), ("original_name", models.CharField(max_length=255)), ("mime_type", models.CharField(max_length=120)), ("size_bytes", models.PositiveIntegerField()), ("uploaded_at", models.DateTimeField(auto_now_add=True)), ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="hub.userprofile"))], options={"ordering": ["uploaded_at"]}),
    ]
