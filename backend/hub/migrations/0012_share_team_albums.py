from django.db import migrations


def share_team_albums(apps, schema_editor):
    MediaAlbum = apps.get_model("hub", "MediaAlbum")
    MediaAsset = apps.get_model("hub", "MediaAsset")

    team_album_ids = MediaAlbum.objects.filter(created_by_role="user").values_list("id", flat=True)
    MediaAlbum.objects.filter(id__in=team_album_ids).update(available_to_media=True)
    MediaAsset.objects.filter(album_id__in=team_album_ids).update(
        available_to_media=True,
        document_status="approved",
    )


class Migration(migrations.Migration):
    dependencies = [("hub", "0011_media_albums")]
    operations = [migrations.RunPython(share_team_albums, migrations.RunPython.noop)]
