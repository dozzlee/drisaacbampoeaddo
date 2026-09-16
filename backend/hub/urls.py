from django.urls import path
from . import views
urlpatterns = [
    path("health/", views.health), path("access/", views.access_session), path("users/", views.users),
    path("tributes/parties", views.tribute_parties),
    path("tributes/files", views.tribute_files),
    path("tributes/files/<uuid:attachment_id>/download", views.download_tribute_file),
    path("tributes/files/<uuid:attachment_id>/edit", views.edit_tribute_file),
    path("tributes/files/<uuid:attachment_id>", views.delete_tribute_file),
    path("tributes/<int:party_id>/files", views.upload_tribute_file),
    path("media", views.media_assets),
    path("media/<uuid:asset_id>/edit", views.edit_media_asset),
    path("media/<uuid:asset_id>/preview", views.preview_media_asset),
    path("media/<uuid:asset_id>/download", views.download_media_asset),
    path("media/<uuid:asset_id>", views.delete_media_asset),
    path("activities", views.activities),
    path("activities/<int:task_id>", views.activity_detail),
    path("activities/subcommittees", views.activity_subcommittees),
    path("activities/subcommittees/<uuid:subcommittee_id>", views.activity_subcommittee_detail),
    path("activities/<int:task_id>/files", views.upload_activity_file),
    path("activities/files/<uuid:attachment_id>/download", views.download_activity_file),
    path("activities/files/<uuid:attachment_id>", views.delete_activity_file),
]
