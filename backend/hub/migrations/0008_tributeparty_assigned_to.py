from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("hub", "0007_tributeattachment_attachment_type")]

    operations = [
        migrations.AddField(
            model_name="tributeparty",
            name="assigned_to",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
