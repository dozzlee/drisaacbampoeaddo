import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from .models import UserProfile

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HubFlowTests(TestCase):
    def test_phone_number_maps_to_one_user(self):
        first = self.client.post("/api/users/", data='{"name":"Ama","phone":"024 123 4567","role":"user"}', content_type="application/json")
        second = self.client.post("/api/users/", data='{"name":"Someone Else","phone":"+233 24 123 4567","role":"admin"}', content_type="application/json")
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(first.json()["user"]["id"], second.json()["user"]["id"])

    def test_upload_list_and_download_tribute_file(self):
        uploaded = SimpleUploadedFile("tribute.pdf", b"tribute-file-content", content_type="application/pdf")
        response = self.client.post("/api/tributes/14/files", {"file": uploaded})
        self.assertEqual(response.status_code, 201)
        record = response.json(); listing = self.client.get("/api/tributes/files").json()
        self.assertEqual(listing["14"][0]["name"], "tribute.pdf")
        download = self.client.get(record["href"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), b"tribute-file-content")
