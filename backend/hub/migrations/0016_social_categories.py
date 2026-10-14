from django.db import migrations


def rename_category(apps, schema_editor, old, new):
    Asset = apps.get_model("hub", "MediaAsset")
    for item in Asset.objects.using(schema_editor.connection.alias).filter(photo_metadata__category=old).iterator():
        item.photo_metadata = {**item.photo_metadata, "category": new}
        item.save(using=schema_editor.connection.alias, update_fields=["photo_metadata"])


def forwards(apps, schema_editor):
    rename_category(apps, schema_editor, "Social / Pictures of travel", "Social / Social")


def backwards(apps, schema_editor):
    rename_category(apps, schema_editor, "Social / Social", "Social / Pictures of travel")


class Migration(migrations.Migration):
    dependencies = [("hub", "0015_replace_photo_categories")]
    operations = [migrations.RunPython(forwards, backwards)]
