from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("hub", "0013_share_all_albums")]
    operations = [migrations.AddField(model_name="mediaasset", name="photo_metadata", field=models.JSONField(default=dict, blank=True))]
