import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from .models import MediaAsset, TributeAttachment, TributeParty, UserProfile

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

    def test_remove_attachment_deletes_metadata_and_stored_file(self):
        party = TributeParty.objects.create(name="Removal Party")
        uploaded = SimpleUploadedFile("remove-me.pdf", b"remove-content", content_type="application/pdf")
        record = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded}).json()["file"]
        attachment = TributeAttachment.objects.get(pk=record["id"])
        stored_path = Path(attachment.file.path)
        self.assertTrue(stored_path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f"/api/tributes/files/{record['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TributeAttachment.objects.filter(pk=record["id"]).exists())
        self.assertFalse(stored_path.exists())

    def test_remove_missing_attachment_returns_404(self):
        response = self.client.delete("/api/tributes/files/00000000-0000-0000-0000-000000000000")
        self.assertEqual(response.status_code, 404)

    def test_media_upload_survives_fresh_client_and_downloads(self):
        uploaded = SimpleUploadedFile("portrait.jpg", b"persistent-image", content_type="image/jpeg")
        response = self.client.post(
            "/api/media",
            {"title": "Official portrait", "assetType": "media", "category": "Official Photographs", "description": "Approved portrait", "file": uploaded},
            HTTP_X_TEAMS_ROLE="admin",
        )
        self.assertEqual(response.status_code, 201)
        record = response.json()["item"]
        listing = Client().get("/api/media").json()["items"]
        self.assertTrue(any(item["id"] == record["id"] for item in listing))
        download = Client().get(record["downloadHref"])
        self.assertEqual(b"".join(download.streaming_content), b"persistent-image")

    def test_media_metadata_edit_and_file_replacement_persist(self):
        original = SimpleUploadedFile("draft.pdf", b"draft", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Draft", "assetType": "document", "category": "Funeral Programme", "description": "First draft", "file": original},
            HTTP_X_TEAMS_ROLE="admin",
        ).json()["item"]
        replacement = SimpleUploadedFile("approved.pdf", b"approved", content_type="application/pdf")
        response = self.client.post(
            f"/api/media/{record['id']}/edit",
            {"title": "Approved programme", "assetType": "document", "category": "Funeral Programme", "description": "Final copy", "labels": "final,print", "status": "approved", "file": replacement},
            HTTP_X_TEAMS_ROLE="admin",
        )
        self.assertEqual(response.status_code, 200)
        updated = response.json()["item"]
        self.assertEqual(updated["id"], record["id"])
        self.assertEqual(updated["labels"], ["final", "print"])
        self.assertEqual(MediaAsset.objects.get(pk=record["id"]).title, "Approved programme")
        download = Client().get(updated["downloadHref"])
        self.assertEqual(b"".join(download.streaming_content), b"approved")

    def test_media_failed_write_does_not_create_record(self):
        uploaded = SimpleUploadedFile("broken.pdf", b"broken", content_type="application/pdf")
        before = MediaAsset.objects.count()
        with patch("django.core.files.storage.FileSystemStorage._save", side_effect=OSError("disk unavailable")):
            response = self.client.post(
                "/api/media",
                {"title": "Broken", "assetType": "document", "category": "Invoices", "description": "Must fail", "file": uploaded},
                HTTP_X_TEAMS_ROLE="admin",
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(MediaAsset.objects.count(), before)

    def test_media_mutations_require_admin_and_invalid_records_are_rejected(self):
        uploaded = SimpleUploadedFile("file.pdf", b"content", content_type="application/pdf")
        denied = self.client.post("/api/media", {"title": "No", "assetType": "document", "category": "Invoices", "description": "No", "file": uploaded})
        self.assertEqual(denied.status_code, 403)
        invalid = SimpleUploadedFile("file.pdf", b"content", content_type="application/pdf")
        response = self.client.post("/api/media", {"title": "", "assetType": "document", "category": "", "description": "", "file": invalid}, HTTP_X_TEAMS_ROLE="admin")
        self.assertEqual(response.status_code, 400)

    def test_media_remove_deletes_metadata_and_file(self):
        uploaded = SimpleUploadedFile("remove.pdf", b"remove", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Remove", "assetType": "document", "category": "Invoices", "description": "Temporary", "file": uploaded},
            HTTP_X_TEAMS_ROLE="admin",
        ).json()["item"]
        asset = MediaAsset.objects.get(pk=record["id"])
        path = Path(asset.file.path)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f"/api/media/{record['id']}", HTTP_X_TEAMS_ROLE="admin")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(path.exists())
        self.assertFalse(MediaAsset.objects.filter(pk=record["id"]).exists())

    def test_media_person_only_lists_shared_non_archived_items(self):
        MediaAsset.objects.create(title="Shared", asset_type="media", category="Portraits", description="Shared", original_name="shared.jpg", mime_type="image/jpeg", external_url="/shared.jpg", available_to_media=True)
        MediaAsset.objects.create(title="Private", asset_type="media", category="Portraits", description="Private", original_name="private.jpg", mime_type="image/jpeg", external_url="/private.jpg", available_to_media=False)
        MediaAsset.objects.create(title="Archived", asset_type="document", category="Minutes", description="Archived", original_name="old.pdf", mime_type="application/pdf", external_url="/old.pdf", available_to_media=True, document_status="archived")
        records = self.client.get("/api/media", HTTP_X_TEAMS_ROLE="media").json()["items"]
        titles = {item["title"] for item in records}
        self.assertIn("Shared", titles)
        self.assertNotIn("Private", titles)
        self.assertNotIn("Archived", titles)

    def test_missing_media_file_returns_safe_404(self):
        uploaded = SimpleUploadedFile("missing.pdf", b"content", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Missing", "assetType": "document", "category": "Invoices", "description": "Missing", "file": uploaded},
            HTTP_X_TEAMS_ROLE="admin",
        ).json()["item"]
        asset = MediaAsset.objects.get(pk=record["id"])
        Path(asset.file.path).unlink()
        response = self.client.get(record["downloadHref"])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "The stored file is unavailable.")
