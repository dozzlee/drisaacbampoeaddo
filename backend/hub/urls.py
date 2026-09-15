from django.urls import path
from . import views
urlpatterns = [
    path("health/", views.health), path("users/", views.users),
    path("tributes/parties", views.tribute_parties),
    path("tributes/files", views.tribute_files),
    path("tributes/files/<uuid:attachment_id>/download", views.download_tribute_file),
    path("tributes/files/<uuid:attachment_id>/edit", views.edit_tribute_file),
    path("tributes/<int:party_id>/files", views.upload_tribute_file),
]
