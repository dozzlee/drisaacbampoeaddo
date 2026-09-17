import tempfile
from os import environ
from pathlib import Path
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from .models import ActivityAttachment, ActivitySubcommittee, ActivityTask, MediaAlbum, MediaAsset, TributeAttachment, TributeParty, UserProfile

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HubFlowTests(TestCase):
    def auth(self, code):
        response = self.client.post("/api/access/", data=f'{{"code":"{code}"}}', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['token']}"}

    def test_uncle_oko_tribute_parties_are_seeded(self):
        expected = {
            "Ministry of Agriculture": {"assignedTo": "Minadi", "mainCommittee": "oko"},
            "Accra Academy": {"assignedTo": "Dr Latt", "mainCommittee": "oko"},
            "New Hope School": {"assignedTo": "Alhagi", "mainCommittee": "oko"},
            "KNUST Katanga": {"assignedTo": "Alhagi", "mainCommittee": "oko"},
        }
        actual = {
            name: {"assignedTo": assigned_to, "mainCommittee": main_committee}
            for name, assigned_to, main_committee in TributeParty.objects.filter(name__in=expected).values_list(
                "name", "assigned_to", "main_committee"
            )
        }
        self.assertEqual(actual, expected)

    def test_uncle_oko_is_a_separate_main_committee(self):
        tasks = ActivityTask.objects.filter(source_key__startswith="oko-")
        self.assertEqual(tasks.count(), 12)
        self.assertFalse(tasks.exclude(main_committee="oko").exists())
        self.assertTrue(ActivitySubcommittee.objects.filter(main_committee="oko", name="Tributes").exists())
        self.assertEqual(
            dict(tasks.filter(source_key__in=["oko-03", "oko-04"]).values_list("source_key", "owner")),
            {"oko-03": "Alhagi", "oko-04": "Alhagi"},
        )

        group = ActivitySubcommittee.objects.create(main_committee="oko", name="Test Oko Group")
        response = self.client.post(
            "/api/activities",
            {"task": "Test Oko task", "mainCommittee": "oko", "subcommitteeId": str(group.id)},
            content_type="application/json",
            **self.auth("ADMIN2026"),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["task"]["mainCommittee"], "oko")

    def test_activity_crud_is_persistent_and_admin_only(self):
        group = ActivitySubcommittee.objects.create(main_committee="funeral", name="Test Logistics")
        payload = {
            "task": "Arrange test transport", "mainCommittee": "funeral",
            "subcommitteeId": str(group.id), "owner": "Ama", "deadline": "2026-10-01",
            "priority": "High", "status": "in-progress", "progress": 40,
            "supportingMembers": "Kojo, Esi", "labels": "transport, urgent",
        }
        denied = self.client.post("/api/activities", payload, content_type="application/json")
        self.assertEqual(denied.status_code, 403)
        created = self.client.post("/api/activities", payload, content_type="application/json", **self.auth("ADMIN2026"))
        self.assertEqual(created.status_code, 201)
        record = created.json()["task"]
        self.assertEqual(record["supportingMembers"], ["Kojo", "Esi"])
        listing = Client().get("/api/activities").json()["tasks"]
        self.assertIn(record["id"], [item["id"] for item in listing])
        payload["progress"] = 100
        payload["status"] = "completed"
        updated = self.client.post(f"/api/activities/{record['id']}", payload, content_type="application/json", **self.auth("ADMIN2026"))
        self.assertEqual(updated.json()["task"]["progress"], 100)

    def test_activity_rejects_invalid_group_and_manages_attachment(self):
        invalid = self.client.post(
            "/api/activities", {"task": "Invalid", "mainCommittee": "funeral", "subcommitteeId": "not-a-uuid"},
            content_type="application/json", **self.auth("ADMIN2026"),
        )
        self.assertEqual(invalid.status_code, 400)
        group = ActivitySubcommittee.objects.create(main_committee="brochure", name="Test Editorial")
        task = ActivityTask.objects.create(title="Proofread", main_committee="brochure", subcommittee=group)
        uploaded = SimpleUploadedFile("notes.pdf", b"activity-notes", content_type="application/pdf")
        response = self.client.post(f"/api/activities/{task.id}/files", {"file": uploaded}, **self.auth("ADMIN2026"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivityAttachment.objects.filter(task=task).count(), 1)
        download = self.client.get(response.json()["file"]["href"])
        self.assertEqual(b"".join(download.streaming_content), b"activity-notes")

    def test_phone_number_maps_to_one_user(self):
        first = self.client.post("/api/users/", data='{"name":"Ama","phone":"024 123 4567"}', content_type="application/json", **self.auth("TEAMS2026"))
        second = self.client.post("/api/users/", data='{"name":"Someone Else","phone":"+233 24 123 4567"}', content_type="application/json", **self.auth("ADMIN2026"))
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 200)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(first.json()["user"]["id"], second.json()["user"]["id"])
        self.assertEqual(first.json()["user"]["role"], "user")
        self.assertEqual(second.json()["user"]["role"], "admin")

    def test_team_code_cannot_open_admin_access_even_for_existing_admin_phone(self):
        admin = self.client.post("/api/users/", data='{"name":"Admin","phone":"024 111 2222"}', content_type="application/json", **self.auth("ADMIN2026"))
        self.assertEqual(admin.json()["user"]["role"], "admin")
        team_auth = self.auth("TEAMS2026")
        team = self.client.post("/api/users/", data='{"name":"Admin","phone":"024 111 2222"}', content_type="application/json", **team_auth)
        self.assertEqual(team.json()["user"]["role"], "user")
        denied = self.client.get("/api/users/", **team_auth)
        self.assertEqual(denied.status_code, 403)
        forged = self.client.get("/api/users/", HTTP_X_TEAMS_ROLE="admin")
        self.assertEqual(forged.status_code, 401)

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

    def test_supporting_files_and_tributes_are_stored_separately(self):
        party = TributeParty.objects.create(name="Two Upload Types")
        supporting = SimpleUploadedFile("request-letter.pdf", b"request", content_type="application/pdf")
        tribute = SimpleUploadedFile("final-tribute.pdf", b"tribute", content_type="application/pdf")

        supporting_response = self.client.post(f"/api/tributes/{party.id}/files", {"file": supporting, "type": "file"})
        tribute_response = self.client.post(f"/api/tributes/{party.id}/files", {"file": tribute, "type": "tribute"})

        self.assertEqual(supporting_response.status_code, 201)
        self.assertEqual(tribute_response.status_code, 201)
        self.assertEqual(supporting_response.json()["file"]["type"], "file")
        self.assertEqual(tribute_response.json()["file"]["type"], "tribute")
        self.assertEqual(set(TributeAttachment.objects.filter(party_id=party.id).values_list("attachment_type", flat=True)), {"file", "tribute"})
        party.refresh_from_db()
        self.assertEqual(party.tribute_status, "Received")

    def test_invalid_tribute_upload_type_is_rejected(self):
        party = TributeParty.objects.create(name="Invalid Type")
        uploaded = SimpleUploadedFile("document.pdf", b"content", content_type="application/pdf")
        response = self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded, "type": "unknown"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TributeAttachment.objects.filter(party_id=party.id).count(), 0)

    def test_create_party_is_returned_to_a_fresh_client(self):
        response = self.client.post(
            "/api/tributes/parties",
            data='{"name":"New Persistent Party","mainCommittee":"oko","phone":"0240000000","assignedTo":"Ama Mensah"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        record = response.json()["party"]
        self.assertIsInstance(record["id"], int)
        self.assertEqual(record["assignedTo"], "Ama Mensah")
        self.assertEqual(record["mainCommittee"], "oko")
        parties = Client().get("/api/tributes/parties").json()["parties"]
        self.assertIn(record, parties)

    def test_responsible_person_update_is_admin_only(self):
        party = TributeParty.objects.create(name="Ownership Test")
        payload = '{"assignedTo":"Kofi Bampoe-Addo"}'
        denied = self.client.post(
            f"/api/tributes/parties/{party.id}",
            data=payload,
            content_type="application/json",
            **self.auth("TEAMS2026"),
        )
        self.assertEqual(denied.status_code, 403)
        updated = self.client.post(
            f"/api/tributes/parties/{party.id}",
            data=payload,
            content_type="application/json",
            **self.auth("ADMIN2026"),
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["party"]["assignedTo"], "Kofi Bampoe-Addo")
        party.refresh_from_db()
        self.assertEqual(party.assigned_to, "Kofi Bampoe-Addo")

    def test_full_tribute_register_exports_as_pdf(self):
        party = TributeParty.objects.create(
            name="Ministry of Agriculture",
            phone="0240000000",
            assigned_to="Sena",
            request_status="Sent",
            tribute_status="Received",
        )
        TributeParty.objects.create(name="Accra Academy", assigned_to="Angelo")
        uploaded = SimpleUploadedFile("ministry-tribute.pdf", b"tribute", content_type="application/pdf")
        self.client.post(f"/api/tributes/{party.id}/files", {"file": uploaded, "type": "tribute"})

        response = self.client.get("/api/tributes/export", **self.auth("TEAMS2026"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("tribute-register-", response["Content-Disposition"])
        self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF"))

        denied = self.client.get("/api/tributes/export", **self.auth("MEDIA2026"))
        self.assertEqual(denied.status_code, 403)

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
            **self.auth("ADMIN2026"),
        )
        self.assertEqual(response.status_code, 201)
        record = response.json()["item"]
        listing = Client().get("/api/media").json()["items"]
        self.assertTrue(any(item["id"] == record["id"] for item in listing))
        download = Client().get(record["downloadHref"])
        self.assertEqual(b"".join(download.streaming_content), b"persistent-image")

    def test_normal_user_can_create_album_and_upload_pictures(self):
        auth = self.auth("TEAMS2026")
        created = self.client.post(
            "/api/media/albums",
            data='{"name":"Family pictures","description":"Shared by family","createdBy":"Ama"}',
            content_type="application/json",
            **auth,
        )
        self.assertEqual(created.status_code, 201)
        album = created.json()["album"]
        self.assertEqual(album["uploadLimitBytes"], 1024 ** 3)
        uploaded = SimpleUploadedFile("family.jpg", b"picture", content_type="image/jpeg")
        response = self.client.post(f"/api/media/albums/{album['id']}/assets", {"file": uploaded}, **auth)
        self.assertEqual(response.status_code, 201)
        detail = self.client.get(f"/api/media/albums/{album['id']}", **auth).json()
        self.assertEqual(detail["album"]["itemCount"], 1)
        self.assertEqual(detail["items"][0]["albumId"], album["id"])

    def test_normal_user_album_limit_is_enforced(self):
        album = MediaAlbum.objects.create(name="At limit", created_by_role="user")
        MediaAsset.objects.create(
            album=album, title="Existing", asset_type="media", category="Photo Albums",
            description="Existing", original_name="existing.jpg", mime_type="image/jpeg",
            external_url="/existing.jpg", size_bytes=1024 ** 3,
        )
        uploaded = SimpleUploadedFile("extra.jpg", b"x", content_type="image/jpeg")
        response = self.client.post(f"/api/media/albums/{album.id}/assets", {"file": uploaded}, **self.auth("TEAMS2026"))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(album.assets.count(), 1)

    def test_media_role_only_sees_shared_albums_and_cannot_create_them(self):
        MediaAlbum.objects.create(name="Shared album", available_to_media=True)
        MediaAlbum.objects.create(name="Private album", available_to_media=False)
        auth = self.auth("MEDIA2026")
        listing = self.client.get("/api/media/albums", **auth).json()["albums"]
        names = {album["name"] for album in listing}
        self.assertIn("Shared album", names)
        self.assertNotIn("Private album", names)
        denied = self.client.post("/api/media/albums", data='{"name":"No"}', content_type="application/json", **auth)
        self.assertEqual(denied.status_code, 403)

    def test_picture_archive_seed_uses_persistent_file_storage_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir) / "family" / "portrait.jpg"
            source.parent.mkdir()
            source.write_bytes(b"optimized-picture")
            with patch.dict(environ, {"PICTURE_ARCHIVE_SOURCE": source_dir}):
                call_command("seed_picture_album")
                call_command("seed_picture_album")
        album = MediaAlbum.objects.get(name="Oko and Atteh Picture Archive")
        records = album.assets.filter(notes="archive-source:family/portrait.jpg")
        self.assertEqual(records.count(), 1)
        item = records.get()
        self.assertTrue(item.file.storage.exists(item.file.name))
        self.assertEqual(item.external_url, "")

    def test_media_metadata_edit_and_file_replacement_persist(self):
        original = SimpleUploadedFile("draft.pdf", b"draft", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Draft", "assetType": "document", "category": "Funeral Programme", "description": "First draft", "file": original},
            **self.auth("ADMIN2026"),
        ).json()["item"]
        replacement = SimpleUploadedFile("approved.pdf", b"approved", content_type="application/pdf")
        response = self.client.post(
            f"/api/media/{record['id']}/edit",
            {"title": "Approved programme", "assetType": "document", "category": "Funeral Programme", "description": "Final copy", "labels": "final,print", "status": "approved", "file": replacement},
            **self.auth("ADMIN2026"),
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
                **self.auth("ADMIN2026"),
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(MediaAsset.objects.count(), before)

    def test_media_mutations_require_admin_and_invalid_records_are_rejected(self):
        uploaded = SimpleUploadedFile("file.pdf", b"content", content_type="application/pdf")
        denied = self.client.post("/api/media", {"title": "No", "assetType": "document", "category": "Invoices", "description": "No", "file": uploaded})
        self.assertEqual(denied.status_code, 403)
        invalid = SimpleUploadedFile("file.pdf", b"content", content_type="application/pdf")
        response = self.client.post("/api/media", {"title": "", "assetType": "document", "category": "", "description": "", "file": invalid}, **self.auth("ADMIN2026"))
        self.assertEqual(response.status_code, 400)

    def test_media_remove_deletes_metadata_and_file(self):
        uploaded = SimpleUploadedFile("remove.pdf", b"remove", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Remove", "assetType": "document", "category": "Invoices", "description": "Temporary", "file": uploaded},
            **self.auth("ADMIN2026"),
        ).json()["item"]
        asset = MediaAsset.objects.get(pk=record["id"])
        path = Path(asset.file.path)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(f"/api/media/{record['id']}", **self.auth("ADMIN2026"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(path.exists())
        self.assertFalse(MediaAsset.objects.filter(pk=record["id"]).exists())

    def test_media_person_only_lists_shared_non_archived_items(self):
        MediaAsset.objects.create(title="Shared", asset_type="media", category="Portraits", description="Shared", original_name="shared.jpg", mime_type="image/jpeg", external_url="/shared.jpg", available_to_media=True)
        MediaAsset.objects.create(title="Private", asset_type="media", category="Portraits", description="Private", original_name="private.jpg", mime_type="image/jpeg", external_url="/private.jpg", available_to_media=False)
        MediaAsset.objects.create(title="Archived", asset_type="document", category="Minutes", description="Archived", original_name="old.pdf", mime_type="application/pdf", external_url="/old.pdf", available_to_media=True, document_status="archived")
        records = self.client.get("/api/media", **self.auth("MEDIA2026")).json()["items"]
        titles = {item["title"] for item in records}
        self.assertIn("Shared", titles)
        self.assertNotIn("Private", titles)
        self.assertNotIn("Archived", titles)

    def test_missing_media_file_returns_safe_404(self):
        uploaded = SimpleUploadedFile("missing.pdf", b"content", content_type="application/pdf")
        record = self.client.post(
            "/api/media",
            {"title": "Missing", "assetType": "document", "category": "Invoices", "description": "Missing", "file": uploaded},
            **self.auth("ADMIN2026"),
        ).json()["item"]
        asset = MediaAsset.objects.get(pk=record["id"])
        Path(asset.file.path).unlink()
        response = self.client.get(record["downloadHref"])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "The stored file is unavailable.")
