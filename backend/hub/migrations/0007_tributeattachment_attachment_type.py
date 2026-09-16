from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("hub", "0006_logistics_uncle_oko")]

    operations = [
        migrations.AddField(
            model_name="tributeattachment",
            name="attachment_type",
            field=models.CharField(
                choices=[("file", "Supporting file"), ("tribute", "Tribute")],
                db_index=True,
                default="file",
                max_length=12,
            ),
        ),
    ]
