from django.db import migrations


def replace_categories(apps, schema_editor):
    Asset = apps.get_model("hub", "MediaAsset")
    mapping = {
        "Childhood": "Biography / Childhood",
        "Katanga": "School / Katanga",
        "Accra Academy": "School / Accra Academy",
        "Travel": "Social / Pictures of travel",
    }
    for item in Asset.objects.using(schema_editor.connection.alias).exclude(photo_metadata={}).iterator():
        metadata = dict(item.photo_metadata)
        old = metadata.get("category", "Uncategorised")
        if old != "Uncategorised":
            metadata["previousCategory"] = old
            metadata["category"] = mapping.get(old, "Uncategorised")
            item.photo_metadata = metadata
            item.save(using=schema_editor.connection.alias, update_fields=["photo_metadata"])


def restore_categories(apps, schema_editor):
    Asset = apps.get_model("hub", "MediaAsset")
    for item in Asset.objects.using(schema_editor.connection.alias).exclude(photo_metadata={}).iterator():
        metadata = dict(item.photo_metadata)
        if "previousCategory" in metadata:
            metadata["category"] = metadata.pop("previousCategory")
            item.photo_metadata = metadata
            item.save(using=schema_editor.connection.alias, update_fields=["photo_metadata"])


class Migration(migrations.Migration):
    dependencies = [("hub", "0014_photo_metadata")]
    operations = [migrations.RunPython(replace_categories, restore_categories)]
