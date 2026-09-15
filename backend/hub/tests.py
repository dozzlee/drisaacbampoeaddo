import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from .models import TributeAttachment, TributeParty, UserProfile

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HubFlowTests(TestCase):
    def test_phone_number_maps_to_one_user(self):
        first = self.client.post("/api/users/", data='{"name":"Ama","phone":"024 123 4567","role":"user"}', content_type="application/json")
        second = self.client.post("/api/users/", data='{"name":"Someone Else","phone":"+233 24 123 4567","role":"admin"}', content_type="application/json")
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(first.json()["user"]["id"], second.json()["user"]["id"])

    def test_upload_list_and_download_tribute_file(self):
        party = TributeParty.objects.create(name="Persistent Party")
        uploaded = SimpleUploadedFile("tribute.pdf", b"tribute-file-content", content_type="application/pdf")
        response = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded})
        self.assertEqual(response.status_code, 201)
        record = response.json()["file"]
        listing = Client().get("/api/tributes/files").json()
        self.assertEqual(listing[str(party.id)][0]["name"], "tribute.pdf")
        download = self.client.get(record["href"])
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), b"tribute-file-content")

    def test_create_party_is_returned_to_a_fresh_client(self):
        response = self.client.post(
            "/api/tributes/parties",
            data='{"name":"New Persistent Party","phone":"0240000000"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        record = response.json()["party"]
        self.assertIsInstance(record["id"], int)
        parties = Client().get("/api/tributes/parties").json()["parties"]
        self.assertIn(record, parties)

    def test_invalid_party_and_unknown_upload_are_rejected(self):
        invalid = self.client.post("/api/tributes/parties", data='{"name":"  "}', content_type="application/json")
        self.assertEqual(invalid.status_code, 400)
        uploaded = SimpleUploadedFile("tribute.pdf", b"content", content_type="application/pdf")
        missing = self.client.post("/api/tributes/999999/files", {"file": uploaded})
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(TributeAttachment.objects.count(), 0)

    def test_failed_file_write_does_not_create_metadata(self):
        party = TributeParty.objects.create(name="Storage Failure Party")
        uploaded = SimpleUploadedFile("tribute.pdf", b"content", content_type="application/pdf")
        with patch("django.core.files.storage.FileSystemStorage._save", side_effect=OSError("disk unavailable")):
            response = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(TributeAttachment.objects.count(), 0)

    def test_missing_stored_file_returns_safe_404(self):
        party = TributeParty.objects.create(name="Missing File Party")
        uploaded = SimpleUploadedFile("tribute.pdf", b"content", content_type="application/pdf")
        record = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded}).json()["file"]
        attachment = TributeAttachment.objects.get(pk=record["id"])
        Path(attachment.file.path).unlink()
        response = self.client.get(record["href"])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "The stored file is unavailable.")

    def test_rename_uploaded_file_persists(self):
        party = TributeParty.objects.create(name="Rename Party")
        uploaded = SimpleUploadedFile("original.pdf", b"original-content", content_type="application/pdf")
        record = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded}).json()["file"]
        response = self.client.post(f"/api/tributes/files/{record['id']}/edit", {"name": "renamed.pdf"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["file"]["name"], "renamed.pdf")
        listing = Client().get("/api/tributes/files").json()
        self.assertEqual(listing[str(party.id)][0]["name"], "renamed.pdf")

    def test_replace_uploaded_file_updates_durable_content(self):
        party = TributeParty.objects.create(name="Replace Party")
        original = SimpleUploadedFile("original.pdf", b"original-content", content_type="application/pdf")
        record = self.client.post(f"/api/tributes/{party.id}/files", {"file": original}).json()["file"]
        replacement = SimpleUploadedFile("replacement.pdf", b"replacement-content", content_type="application/pdf")
        response = self.client.post(
            f"/api/tributes/files/{record['id']}/edit",
            {"name": "final-tribute.pdf", "file": replacement},
        )
        self.assertEqual(response.status_code, 200)
        updated = response.json()["file"]
        self.assertEqual(updated["id"], record["id"])
        self.assertEqual(updated["name"], "final-tribute.pdf")
        download = Client().get(updated["href"])
        self.assertEqual(b"".join(download.streaming_content), b"replacement-content")

    def test_edit_missing_attachment_returns_404(self):
        response = self.client.post(
            "/api/tributes/files/00000000-0000-0000-0000-000000000000/edit",
            {"name": "missing.pdf"},
        )
        self.assertEqual(response.status_code, 404)
