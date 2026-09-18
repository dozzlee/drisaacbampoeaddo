from django.db import migrations


def share_all_albums(apps, schema_editor):
    MediaAlbum = apps.get_model("hub", "MediaAlbum")
    MediaAsset = apps.get_model("hub", "MediaAsset")

    album_ids = MediaAlbum.objects.values_list("id", flat=True)
    MediaAlbum.objects.update(available_to_media=True)
    MediaAsset.objects.filter(album_id__in=album_ids).update(
        available_to_media=True,
        document_status="approved",
    )


class Migration(migrations.Migration):
    dependencies = [("hub", "0012_share_team_albums")]
    operations = [migrations.RunPython(share_all_albums, migrations.RunPython.noop)]
