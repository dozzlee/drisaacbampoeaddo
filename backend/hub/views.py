import json
import logging
import re
import shutil
import tempfile
import uuid
import zipfile
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import signing
from django.db import IntegrityError, connection, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.text import slugify
from django.http import FileResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .models import ActivityAttachment, ActivitySubcommittee, ActivityTask, MediaAlbum, MediaAsset, TributeAttachment, TributeParty, UserProfile, normalize_phone
from .pdf_exports import build_tribute_register_pdf

logger = logging.getLogger(__name__)

ACCESS_TOKEN_SALT = "hub.access.v1"

def user_json(user, role=None): return {"id": str(user.id), "name": user.full_name, "phone": user.phone, "role": role or user.role}

def access_role(request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        payload = signing.loads(authorization[7:], salt=ACCESS_TOKEN_SALT, max_age=settings.TEAM_ACCESS_TOKEN_MAX_AGE)
        role = payload.get("role")
        return role if role in UserProfile.Role.values else None
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def access_session(request):
    if request.method == "GET":
        role = access_role(request)
        if not role:
            return JsonResponse({"error": "Your access session is invalid or has expired."}, status=401)
        return JsonResponse({"role": role})
    try:
        payload = json.loads(request.body)
        code = re.sub(r"[-\s]", "", str(payload.get("code", "")).upper())
        role = settings.TEAM_ACCESS_CODES.get(code)
        if not role:
            return JsonResponse({"error": "That code was not recognised. Check it and try again."}, status=403)
        token = signing.dumps({"role": role}, salt=ACCESS_TOKEN_SALT, compress=True)
        return JsonResponse({"role": role, "token": token})
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Enter a valid access code."}, status=400)

@require_GET
def health(request):
    try:
        with connection.cursor() as cursor: cursor.execute("SELECT 1"); cursor.fetchone()
        return JsonResponse({"status": "ok", "database": "postgresql"})
    except Exception: return JsonResponse({"status": "error", "database": "unavailable"}, status=503)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def users(request):
    role = access_role(request)
    if not role:
        return JsonResponse({"error": "A valid access session is required."}, status=401)
    if request.method == "GET":
        if role != UserProfile.Role.ADMIN:
            return JsonResponse({"error": "Administrator access is required."}, status=403)
        return JsonResponse({"users": [user_json(user) for user in UserProfile.objects.order_by("full_name")]})
    try:
        payload = json.loads(request.body)
        normalized = normalize_phone(payload.get("phone"))
        existing = UserProfile.objects.filter(normalized_phone=normalized).first()
        if existing: return JsonResponse({"user": user_json(existing, role), "created": False})
        user = UserProfile.objects.create(full_name=payload.get("name", "").strip(), phone=payload.get("phone", "").strip(), role=role)
        return JsonResponse({"user": user_json(user, role), "created": True}, status=201)
    except (ValidationError, ValueError, KeyError) as error: return JsonResponse({"error": str(error)}, status=400)
    except IntegrityError: return JsonResponse({"error": "This phone number already belongs to a user."}, status=409)

def attachment_json(item):
    return {"id": str(item.id), "name": item.original_name, "type": item.attachment_type, "href": f"/api/tributes/files/{item.id}/download", "size": item.size_bytes, "uploadedAt": item.uploaded_at.isoformat()}

ALLOWED_TRIBUTE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

def validate_tribute_upload(uploaded):
    if uploaded.content_type not in ALLOWED_TRIBUTE_TYPES:
        return JsonResponse({"error": "This file type is not supported."}, status=400)
    if uploaded.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "Files must be smaller than 10 MB."}, status=413)
    return None

def party_json(party):
    return {"id": party.id, "name": party.name, "phone": party.phone, "assignedTo": party.assigned_to, "mainCommittee": party.main_committee, "request": party.request_status, "tribute": party.tribute_status, "createdAt": party.created_at.isoformat()}

@csrf_exempt
@require_http_methods(["GET", "POST"])
def tribute_parties(request):
    if request.method == "GET":
        return JsonResponse({"parties": [party_json(party) for party in TributeParty.objects.all()]})
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()
        phone = str(payload.get("phone", "")).strip()
        assigned_to = str(payload.get("assignedTo", "")).strip()
        main_committee = str(payload.get("mainCommittee", TributeParty.MainCommittee.GENERAL)).strip().lower()
        if not name:
            return JsonResponse({"error": "Person or organisation is required."}, status=400)
        if main_committee not in TributeParty.MainCommittee.values:
            return JsonResponse({"error": "Choose a valid main committee."}, status=400)
        party = TributeParty.objects.create(name=name, phone=phone, assigned_to=assigned_to, main_committee=main_committee)
        logger.info("tribute_party_created id=%s", party.id)
        return JsonResponse({"party": party_json(party)}, status=201)
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning("tribute_party_create_invalid_payload")
        return JsonResponse({"error": "Invalid party data."}, status=400)

@csrf_exempt
@require_POST
def tribute_party_detail(request, party_id):
    denied = admin_required(request)
    if denied: return denied
    party = get_object_or_404(TributeParty, pk=party_id)
    try:
        payload = json.loads(request.body)
        assigned_to = str(payload.get("assignedTo", party.assigned_to)).strip()
        if len(assigned_to) > 255:
            return JsonResponse({"error": "Responsible person must be 255 characters or fewer."}, status=400)
        party.assigned_to = assigned_to
        party.save(update_fields=["assigned_to"])
        return JsonResponse({"party": party_json(party)})
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid tribute record."}, status=400)

@require_GET
def export_tributes_pdf(request):
    role = access_role(request)
    if not role:
        return JsonResponse({"error": "A valid access session is required."}, status=401)
    if role == UserProfile.Role.MEDIA:
        return JsonResponse({"error": "Team or administrator access is required."}, status=403)
    parties = list(TributeParty.objects.all())
    attachments_by_party = {}
    latest_by_party = {party.id: party.created_at for party in parties}
    for item in TributeAttachment.objects.all():
        attachments_by_party.setdefault(item.party_id, []).append(item)
        latest_by_party[item.party_id] = max(latest_by_party.get(item.party_id, item.uploaded_at), item.uploaded_at)
    parties.sort(key=lambda party: (latest_by_party.get(party.id, party.created_at), party.id), reverse=True)
    pdf = build_tribute_register_pdf(parties, attachments_by_party)
    filename = f"tribute-register-{timezone.localdate().isoformat()}.pdf"
    return FileResponse(pdf, as_attachment=True, filename=filename, content_type="application/pdf")

@require_GET
def tribute_files(request):
    records = {}
    for item in TributeAttachment.objects.all(): records.setdefault(str(item.party_id), []).append(attachment_json(item))
    return JsonResponse(records)

@csrf_exempt
@require_POST
def upload_tribute_file(request, party_id):
    party = TributeParty.objects.filter(pk=party_id).first()
    if not party:
        return JsonResponse({"error": "Tribute party not found."}, status=404)
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    attachment_type = str(request.POST.get("type", TributeAttachment.AttachmentType.FILE)).strip().lower()
    if attachment_type not in TributeAttachment.AttachmentType.values:
        return JsonResponse({"error": "Choose a valid upload type."}, status=400)
    validation_error = validate_tribute_upload(uploaded)
    if validation_error: return validation_error
    try:
        with transaction.atomic():
            item = TributeAttachment.objects.create(party_id=party_id, attachment_type=attachment_type, file=uploaded, original_name=uploaded.name, mime_type=uploaded.content_type, size_bytes=uploaded.size)
            if attachment_type == TributeAttachment.AttachmentType.TRIBUTE and party.tribute_status != "Received":
                party.tribute_status = "Received"
                party.save(update_fields=["tribute_status"])
        logger.info("tribute_file_created id=%s party_id=%s type=%s size=%s", item.id, party_id, attachment_type, uploaded.size)
        return JsonResponse({"file": attachment_json(item)}, status=201)
    except Exception:
        logger.exception("tribute_file_create_failed party_id=%s", party_id)
        return JsonResponse({"error": "The file could not be saved."}, status=500)

@csrf_exempt
@require_POST
def edit_tribute_file(request, attachment_id):
    item = get_object_or_404(TributeAttachment, pk=attachment_id)
    replacement = request.FILES.get("file")
    new_name = str(request.POST.get("name", "")).strip()
    attachment_type = str(request.POST.get("type", item.attachment_type)).strip().lower()
    if attachment_type not in TributeAttachment.AttachmentType.values:
        return JsonResponse({"error": "Choose a valid upload type."}, status=400)
    if not new_name and not replacement:
        return JsonResponse({"error": "Enter a file name or choose a replacement file."}, status=400)
    if replacement:
        validation_error = validate_tribute_upload(replacement)
        if validation_error: return validation_error
    old_storage = item.file.storage
    old_path = item.file.name
    old_type = item.attachment_type
    try:
        with transaction.atomic():
            if replacement:
                item.file = replacement
                item.mime_type = replacement.content_type
                item.size_bytes = replacement.size
            item.original_name = new_name or replacement.name
            item.attachment_type = attachment_type
            item.save()
            party = TributeParty.objects.filter(pk=item.party_id).first()
            if party and attachment_type == TributeAttachment.AttachmentType.TRIBUTE and party.tribute_status != "Received":
                party.tribute_status = "Received"
                party.save(update_fields=["tribute_status"])
            if party and old_type == TributeAttachment.AttachmentType.TRIBUTE and attachment_type != old_type and not TributeAttachment.objects.filter(party_id=item.party_id, attachment_type=TributeAttachment.AttachmentType.TRIBUTE).exclude(pk=item.pk).exists():
                party.tribute_status = "Not recorded"
                party.save(update_fields=["tribute_status"])
            if replacement and old_path and old_path != item.file.name:
                transaction.on_commit(lambda: old_storage.delete(old_path))
        logger.info("tribute_file_updated id=%s replaced=%s", item.id, bool(replacement))
        return JsonResponse({"file": attachment_json(item)})
    except Exception:
        logger.exception("tribute_file_update_failed id=%s", item.id)
        return JsonResponse({"error": "The file could not be updated."}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_tribute_file(request, attachment_id):
    item = get_object_or_404(TributeAttachment, pk=attachment_id)
    storage = item.file.storage
    stored_path = item.file.name
    party_id = item.party_id
    attachment_type = item.attachment_type
    try:
        with transaction.atomic():
            item.delete()
            if attachment_type == TributeAttachment.AttachmentType.TRIBUTE and not TributeAttachment.objects.filter(party_id=party_id, attachment_type=TributeAttachment.AttachmentType.TRIBUTE).exists():
                TributeParty.objects.filter(pk=party_id).update(tribute_status="Not recorded")
            if stored_path:
                transaction.on_commit(lambda: storage.delete(stored_path))
        logger.info("tribute_file_deleted id=%s", attachment_id)
        return JsonResponse({"deleted": True, "id": str(attachment_id)})
    except Exception:
        logger.exception("tribute_file_delete_failed id=%s", attachment_id)
        return JsonResponse({"error": "The file could not be removed."}, status=500)

@require_GET
def download_tribute_file(request, attachment_id):
    item = get_object_or_404(TributeAttachment, pk=attachment_id)
    try:
        return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.original_name, content_type=item.mime_type)
    except (FileNotFoundError, OSError):
        logger.warning("tribute_file_missing id=%s", item.id)
        return JsonResponse({"error": "The stored file is unavailable."}, status=404)

SAFE_INLINE_LIBRARY_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/avif",
    "video/mp4", "video/quicktime", "video/webm", "audio/mpeg", "audio/wav", "audio/mp4",
    "application/pdf", "text/plain",
}

USER_ALBUM_LIMIT_BYTES = 1024 * 1024 * 1024
ALBUM_FILE_LIMIT_BYTES = 100 * 1024 * 1024

def request_role(request):
    return access_role(request) or UserProfile.Role.USER

def admin_required(request):
    if request_role(request) != "admin":
        return JsonResponse({"error": "Administrator access is required."}, status=403)
    return None

def validate_library_upload(uploaded):
    # Other file formats remain downloadable attachments, never inline documents.
    if not uploaded.size:
        return JsonResponse({"error": "The selected file is empty."}, status=400)
    if uploaded.size > 100 * 1024 * 1024:
        return JsonResponse({"error": "Files must be smaller than 100 MB."}, status=413)
    return None

def media_asset_json(item):
    has_file = bool(item.file)
    preview_href = f"/api/media/{item.id}/preview" if has_file else item.external_url
    download_href = f"/api/media/{item.id}/download" if has_file else item.external_url
    return {
        "id": str(item.id), "albumId": str(item.album_id) if item.album_id else "", "title": item.title, "assetType": item.asset_type,
        "category": item.category, "description": item.description,
        "originalName": item.original_name, "mimeType": item.mime_type,
        "size": item.size_bytes, "labels": item.labels, "dateCreated": item.date_created.isoformat() if item.date_created else "",
        "eventActivity": item.event_activity, "responsibleCommittee": item.responsible_committee,
        "uploadedBy": item.uploaded_by_name, "ownerContact": item.owner_contact, "phone": item.phone,
        "confidentiality": item.confidentiality, "version": item.version,
        "status": item.document_status, "notes": item.notes, "available": item.available_to_media,
        "previewHref": preview_href, "downloadHref": download_href,
        "uploadedAt": item.uploaded_at.isoformat(), "updatedAt": item.updated_at.isoformat(),
        "missing": not has_file and not bool(item.external_url),
    }

def album_asset_queryset(album, role):
    records = album.assets.all()
    if role == UserProfile.Role.MEDIA:
        records = records.filter(available_to_media=True).exclude(document_status=MediaAsset.Status.ARCHIVED)
    return records

def media_album_json(album, role):
    records = album_asset_queryset(album, role)
    total_size = records.aggregate(total=Sum("size_bytes"))["total"] or 0
    cover = records.filter(mime_type__startswith="image/").first()
    return {
        "id": str(album.id), "name": album.name, "description": album.description,
        "createdBy": album.created_by_name, "createdByRole": album.created_by_role,
        "available": album.available_to_media, "itemCount": records.count(), "totalSize": total_size,
        "coverUrl": media_asset_json(cover)["previewHref"] if cover else "",
        "uploadLimitBytes": None if role == UserProfile.Role.ADMIN else USER_ALBUM_LIMIT_BYTES,
        "createdAt": album.created_at.isoformat(), "updatedAt": album.updated_at.isoformat(),
    }

def album_write_role(request):
    role = access_role(request)
    if not role:
        return None, JsonResponse({"error": "A valid access session is required."}, status=401)
    if role not in {UserProfile.Role.ADMIN, UserProfile.Role.USER}:
        return role, JsonResponse({"error": "This role cannot upload albums."}, status=403)
    return role, None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def media_albums(request):
    role = access_role(request)
    if not role:
        return JsonResponse({"error": "A valid access session is required."}, status=401)
    if request.method == "GET":
        records = MediaAlbum.objects.all()
        if role == UserProfile.Role.MEDIA:
            records = records.filter(available_to_media=True)
        return JsonResponse({"albums": [media_album_json(album, role) for album in records]})
    role, denied = album_write_role(request)
    if denied: return denied
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()
        if not name:
            return JsonResponse({"error": "Album name is required."}, status=400)
        if len(name) > 255:
            return JsonResponse({"error": "Album name must be 255 characters or fewer."}, status=400)
        album = MediaAlbum.objects.create(
            name=name,
            description=str(payload.get("description", "")).strip(),
            created_by_name=str(payload.get("createdBy", "")).strip(),
            created_by_role=role,
            available_to_media=role == UserProfile.Role.ADMIN and bool(payload.get("available", False)),
        )
        return JsonResponse({"album": media_album_json(album, role)}, status=201)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Enter valid album details."}, status=400)

@require_GET
def media_album_assets(request, album_id):
    role = access_role(request)
    if not role:
        return JsonResponse({"error": "A valid access session is required."}, status=401)
    album = get_object_or_404(MediaAlbum, pk=album_id)
    if role == UserProfile.Role.MEDIA and not album.available_to_media:
        return JsonResponse({"error": "Album not found."}, status=404)
    return JsonResponse({"album": media_album_json(album, role), "items": [media_asset_json(item) for item in album_asset_queryset(album, role)]})

@csrf_exempt
@require_POST
def edit_media_album(request, album_id):
    role, denied = album_write_role(request)
    if denied: return denied
    album = get_object_or_404(MediaAlbum, pk=album_id)
    if role != UserProfile.Role.ADMIN and album.created_by_role != UserProfile.Role.USER:
        return JsonResponse({"error": "Only an administrator can edit this album."}, status=403)
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()
        if not name:
            return JsonResponse({"error": "Album name is required."}, status=400)
        if len(name) > 255:
            return JsonResponse({"error": "Album name must be 255 characters or fewer."}, status=400)
        album.name = name
        album.description = str(payload.get("description", "")).strip()
        if role == UserProfile.Role.ADMIN and "available" in payload:
            album.available_to_media = bool(payload["available"])
        album.save(update_fields=["name", "description", "available_to_media", "updated_at"])
        if role == UserProfile.Role.ADMIN and "available" in payload:
            album.assets.update(available_to_media=album.available_to_media)
        return JsonResponse({"album": media_album_json(album, role)})
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Enter valid album details."}, status=400)

@csrf_exempt
@require_POST
def download_media_album(request, album_id):
    """Build a read-only archive from stored, role-visible album files."""
    role = access_role(request)
    if not role:
        return JsonResponse({"error": "A valid access session is required."}, status=401)
    album = get_object_or_404(MediaAlbum, pk=album_id)
    if role == UserProfile.Role.MEDIA and not album.available_to_media:
        return JsonResponse({"error": "Album not found."}, status=404)
    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict):
            raise ValueError
        ids = payload.get("ids")
        if "ids" in payload:
            if not isinstance(ids, list) or not ids or len(ids) > 10000:
                raise ValueError
            ids = {uuid.UUID(value) for value in ids if isinstance(value, str)}
            if len(ids) != len(set(payload["ids"])):
                raise ValueError
    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        return JsonResponse({"error": "Choose one or more valid pictures."}, status=400)
    records = album_asset_queryset(album, role)
    if ids is not None:
        records = records.filter(id__in=ids)
        if records.count() != len(ids):
            return JsonResponse({"error": "One or more selected pictures are unavailable."}, status=404)
    if not records.exists():
        return JsonResponse({"error": "This album has no downloadable pictures."}, status=400)
    # Spill large archives to temporary disk; do not hold an album in server RAM.
    archive = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b")
    try:
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as bundle:
            for index, item in enumerate(records.iterator(), start=1):
                if not item.file:
                    raise FileNotFoundError
                name = (item.original_name or item.file.name).replace("\\", "/").rsplit("/", 1)[-1]
                name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip(". ") or "picture"
                # Prefixes prevent duplicate names and archive path traversal.
                with item.file.open("rb") as source, bundle.open(f"{index:04d}-{name}", "w", force_zip64=True) as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
        archive.seek(0)
        filename = (slugify(album.name)[:100] or "photo-album") + ("-selected" if ids is not None else "") + ".zip"
        return FileResponse(archive, as_attachment=True, filename=filename, content_type="application/zip")
    except (FileNotFoundError, OSError):
        archive.close()
        logger.warning("media_album_download_unavailable album_id=%s", album_id)
        return JsonResponse({"error": "A picture is unavailable. Try downloading the remaining pictures individually."}, status=409)
    except Exception:
        archive.close()
        logger.exception("media_album_download_failed album_id=%s", album_id)
        return JsonResponse({"error": "The album download could not be prepared. Please try again."}, status=500)

@csrf_exempt
@require_POST
def upload_media_album_asset(request, album_id):
    role, denied = album_write_role(request)
    if denied: return denied
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "Choose a file to upload."}, status=400)
    if not uploaded.size:
        return JsonResponse({"error": "The selected file is empty."}, status=400)
    if uploaded.size > ALBUM_FILE_LIMIT_BYTES:
        return JsonResponse({"error": "Each file must be smaller than 100 MB."}, status=413)
    try:
        with transaction.atomic():
            album = MediaAlbum.objects.select_for_update().get(pk=album_id)
            used = album.assets.aggregate(total=Sum("size_bytes"))["total"] or 0
            if role == UserProfile.Role.USER and used + uploaded.size > USER_ALBUM_LIMIT_BYTES:
                return JsonResponse({"error": "This album has reached the 1 GB user upload limit."}, status=413)
            title = str(request.POST.get("title", "")).strip() or uploaded.name.rsplit(".", 1)[0]
            mime_type = uploaded.content_type or "application/octet-stream"
            asset_type = MediaAsset.AssetType.MEDIA if mime_type.startswith(("image/", "video/", "audio/")) else MediaAsset.AssetType.DOCUMENT
            item = MediaAsset(
                album=album, title=title, asset_type=asset_type,
                category="Albums", description=str(request.POST.get("description", album.description or "Album file.")).strip(),
                original_name=uploaded.name, mime_type=mime_type, size_bytes=uploaded.size,
                uploaded_by_name=str(request.POST.get("uploadedBy", "")).strip(),
                document_status=MediaAsset.Status.APPROVED if role == UserProfile.Role.ADMIN else MediaAsset.Status.DRAFT,
                available_to_media=album.available_to_media and role == UserProfile.Role.ADMIN,
            )
            item.file = uploaded
            item.save()
            album.updated_at = timezone.now()
            album.save(update_fields=["updated_at"])
        logger.info("media_album_asset_created album_id=%s asset_id=%s size=%s", album_id, item.id, uploaded.size)
        return JsonResponse({"album": media_album_json(album, role), "item": media_asset_json(item)}, status=201)
    except MediaAlbum.DoesNotExist:
        return JsonResponse({"error": "Album not found."}, status=404)
    except Exception:
        logger.exception("media_album_asset_create_failed album_id=%s", album_id)
        return JsonResponse({"error": "The file could not be saved."}, status=500)

def split_labels(value):
    return [label.strip() for label in str(value or "").split(",") if label.strip()][:20]

def apply_media_fields(item, data):
    item.title = str(data.get("title", item.title)).strip()
    item.asset_type = str(data.get("assetType", item.asset_type)).strip().lower()
    item.category = str(data.get("category", item.category)).strip()
    item.description = str(data.get("description", item.description)).strip()
    item.labels = split_labels(data.get("labels", ",".join(item.labels)))
    if "dateCreated" in data:
        item.date_created = str(data.get("dateCreated", "")).strip() or None
    item.event_activity = str(data.get("eventActivity", item.event_activity)).strip()
    item.responsible_committee = str(data.get("responsibleCommittee", item.responsible_committee)).strip()
    item.uploaded_by_name = str(data.get("uploadedBy", item.uploaded_by_name)).strip()
    item.owner_contact = str(data.get("ownerContact", item.owner_contact)).strip()
    item.phone = str(data.get("phone", item.phone)).strip()
    item.confidentiality = str(data.get("confidentiality", item.confidentiality or "Internal")).strip()
    item.version = str(data.get("version", item.version or "1.0")).strip()
    item.document_status = str(data.get("status", item.document_status or "draft")).strip().lower()
    item.notes = str(data.get("notes", item.notes)).strip()
    if "available" in data:
        item.available_to_media = str(data.get("available")).lower() in {"true", "1", "yes", "on"}

def validate_media_fields(item):
    if not item.title or not item.category or not item.description:
        return "Title, category and description are required."
    if item.asset_type not in MediaAsset.AssetType.values:
        return "Choose Media or Document as the file type."
    if item.document_status not in MediaAsset.Status.values:
        return "Choose a valid document status."
    return None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def media_assets(request):
    if request.method == "GET":
        records = MediaAsset.objects.filter(album__isnull=True)
        if request_role(request) == "media":
            records = records.filter(available_to_media=True).exclude(document_status=MediaAsset.Status.ARCHIVED)
        return JsonResponse({"items": [media_asset_json(item) for item in records]})
    role = access_role(request)
    if role not in {UserProfile.Role.ADMIN, UserProfile.Role.USER}:
        return JsonResponse({"error": "Team access is required to upload files."}, status=403)
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    upload_error = validate_library_upload(uploaded)
    if upload_error: return upload_error
    item = MediaAsset(original_name=uploaded.name, mime_type=uploaded.content_type or "application/octet-stream", size_bytes=uploaded.size)
    apply_media_fields(item, request.POST)
    if role != UserProfile.Role.ADMIN:
        item.available_to_media = False
        item.document_status = MediaAsset.Status.DRAFT
    field_error = validate_media_fields(item)
    if field_error: return JsonResponse({"error": field_error}, status=400)
    try:
        with transaction.atomic():
            item.file = uploaded
            item.save()
        logger.info("media_asset_created id=%s size=%s", item.id, uploaded.size)
        return JsonResponse({"item": media_asset_json(item)}, status=201)
    except Exception:
        logger.exception("media_asset_create_failed")
        return JsonResponse({"error": "The file could not be saved."}, status=500)

@csrf_exempt
@require_POST
def edit_media_asset(request, asset_id):
    denied = admin_required(request)
    if denied: return denied
    item = get_object_or_404(MediaAsset, pk=asset_id)
    replacement = request.FILES.get("file")
    if replacement:
        upload_error = validate_library_upload(replacement)
        if upload_error: return upload_error
    apply_media_fields(item, request.POST)
    field_error = validate_media_fields(item)
    if field_error: return JsonResponse({"error": field_error}, status=400)
    old_storage = item.file.storage if item.file else None
    old_path = item.file.name if item.file else ""
    try:
        with transaction.atomic():
            if replacement:
                item.file = replacement
                item.external_url = ""
                item.original_name = replacement.name
                item.mime_type = replacement.content_type
                item.size_bytes = replacement.size
            item.save()
            if replacement and old_storage and old_path and old_path != item.file.name:
                transaction.on_commit(lambda: old_storage.delete(old_path))
        logger.info("media_asset_updated id=%s replaced=%s", item.id, bool(replacement))
        return JsonResponse({"item": media_asset_json(item)})
    except Exception:
        logger.exception("media_asset_update_failed id=%s", item.id)
        return JsonResponse({"error": "The media record could not be updated."}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_media_asset(request, asset_id):
    denied = admin_required(request)
    if denied: return denied
    item = get_object_or_404(MediaAsset, pk=asset_id)
    storage = item.file.storage if item.file else None
    path = item.file.name if item.file else ""
    try:
        with transaction.atomic():
            item.delete()
            if storage and path: transaction.on_commit(lambda: storage.delete(path))
        logger.info("media_asset_deleted id=%s", asset_id)
        return JsonResponse({"deleted": True, "id": str(asset_id)})
    except Exception:
        logger.exception("media_asset_delete_failed id=%s", asset_id)
        return JsonResponse({"error": "The media record could not be removed."}, status=500)

def media_file_response(item, attachment):
    if item.file:
        try:
            safe_inline = item.mime_type in SAFE_INLINE_LIBRARY_TYPES
            response = FileResponse(item.file.open("rb"), as_attachment=attachment or not safe_inline,
                                    filename=item.original_name, content_type=item.mime_type if safe_inline else "application/octet-stream")
            response["X-Content-Type-Options"] = "nosniff"
            return response
        except (FileNotFoundError, OSError):
            logger.warning("media_asset_file_missing id=%s", item.id)
            return JsonResponse({"error": "The stored file is unavailable."}, status=404)
    if item.external_url: return HttpResponseRedirect(item.external_url)
    return JsonResponse({"error": "The stored file is unavailable."}, status=404)

@require_GET
def preview_media_asset(request, asset_id):
    return media_file_response(get_object_or_404(MediaAsset, pk=asset_id), False)

@require_GET
def download_media_asset(request, asset_id):
    return media_file_response(get_object_or_404(MediaAsset, pk=asset_id), True)

def activity_attachment_json(item):
    return {"id": str(item.id), "name": item.original_name, "size": item.size_bytes, "href": f"/api/activities/files/{item.id}/download"}

def subcommittee_json(item):
    return {"id": str(item.id), "mainCommittee": item.main_committee, "name": item.name, "color": item.color, "active": item.active}

def activity_json(item):
    return {
        "id": item.id, "task": item.title, "mainCommittee": item.main_committee,
        "subcommitteeId": str(item.subcommittee_id) if item.subcommittee_id else "",
        "subcommittee": item.subcommittee.name if item.subcommittee else "Needs Classification",
        "color": item.subcommittee.color if item.subcommittee else "#8A8F98",
        "owner": item.owner, "supportingMembers": item.supporting_members,
        "startDate": item.start_date.isoformat() if item.start_date else "",
        "deadline": item.deadline.isoformat() if item.deadline else "",
        "priority": item.priority, "status": item.status, "progress": item.progress,
        "notes": item.notes, "labels": item.labels, "updatedAt": item.updated_at.isoformat(),
        "attachments": [activity_attachment_json(file) for file in item.attachments.all()],
    }

def apply_activity_fields(item, data):
    item.title = str(data.get("task", item.title)).strip()
    item.main_committee = str(data.get("mainCommittee", item.main_committee)).strip()
    subcommittee_id = str(data.get("subcommitteeId", item.subcommittee_id or "")).strip()
    try:
        item.subcommittee = ActivitySubcommittee.objects.filter(pk=subcommittee_id, main_committee=item.main_committee).first() if subcommittee_id else None
    except (ValidationError, ValueError):
        item.subcommittee = None
    item.owner = str(data.get("owner", item.owner)).strip()
    item.supporting_members = split_labels(data.get("supportingMembers", ",".join(item.supporting_members)))
    if "startDate" in data: item.start_date = str(data.get("startDate", "")).strip() or None
    if "deadline" in data: item.deadline = str(data.get("deadline", "")).strip() or None
    item.priority = str(data.get("priority", item.priority or "Normal")).strip()
    item.status = str(data.get("status", item.status or ActivityTask.Status.NOT_STARTED)).strip()
    if "progress" in data:
        item.progress = max(0, min(100, int(data.get("progress") or 0)))
    item.notes = str(data.get("notes", item.notes)).strip()
    item.labels = split_labels(data.get("labels", ",".join(item.labels)))

def validate_activity(item):
    if not item.title: return "Task is required."
    if item.main_committee not in ActivityTask.MainCommittee.values: return "Choose a valid main committee."
    if item.status not in ActivityTask.Status.values: return "Choose a valid task status."
    if not item.subcommittee: return "Choose a subcommittee."
    return None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def activities(request):
    if request.method == "GET":
        records = ActivityTask.objects.select_related("subcommittee").prefetch_related("attachments")
        return JsonResponse({"tasks": [activity_json(item) for item in records]})
    denied = admin_required(request)
    if denied: return denied
    item = ActivityTask()
    try:
        apply_activity_fields(item, json.loads(request.body))
        error = validate_activity(item)
        if error: return JsonResponse({"error": error}, status=400)
        item.save()
        item.refresh_from_db()
        logger.info("activity_created id=%s", item.id)
        return JsonResponse({"task": activity_json(item)}, status=201)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid task data."}, status=400)

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def activity_detail(request, task_id):
    denied = admin_required(request)
    if denied: return denied
    item = get_object_or_404(ActivityTask, pk=task_id)
    if request.method == "DELETE":
        paths = [(file.file.storage, file.file.name) for file in item.attachments.all() if file.file]
        with transaction.atomic():
            item.delete()
            for storage, path in paths: transaction.on_commit(lambda s=storage, p=path: s.delete(p))
        logger.info("activity_deleted id=%s", task_id)
        return JsonResponse({"deleted": True, "id": task_id})
    try:
        apply_activity_fields(item, json.loads(request.body))
        error = validate_activity(item)
        if error: return JsonResponse({"error": error}, status=400)
        item.save()
        item.refresh_from_db()
        logger.info("activity_updated id=%s", item.id)
        return JsonResponse({"task": activity_json(item)})
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid task data."}, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def activity_subcommittees(request):
    if request.method == "GET":
        return JsonResponse({"subcommittees": [subcommittee_json(item) for item in ActivitySubcommittee.objects.all()]})
    denied = admin_required(request)
    if denied: return denied
    try:
        payload = json.loads(request.body)
        main = str(payload.get("mainCommittee", "")).strip()
        name = str(payload.get("name", "")).strip()
        color = str(payload.get("color", "#5679C8")).strip()
        if main not in ActivitySubcommittee.MainCommittee.values or not name or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            return JsonResponse({"error": "Enter a valid committee, name and colour."}, status=400)
        item = ActivitySubcommittee.objects.create(main_committee=main, name=name, color=color)
        return JsonResponse({"subcommittee": subcommittee_json(item)}, status=201)
    except (json.JSONDecodeError, IntegrityError):
        return JsonResponse({"error": "That subcommittee already exists or the data is invalid."}, status=400)

@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def activity_subcommittee_detail(request, subcommittee_id):
    denied = admin_required(request)
    if denied: return denied
    item = get_object_or_404(ActivitySubcommittee, pk=subcommittee_id)
    if request.method == "DELETE":
        if item.tasks.exists(): return JsonResponse({"error": "Move or merge this subcommittee's tasks before removing it."}, status=409)
        item.delete()
        return JsonResponse({"deleted": True})
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", item.name)).strip()
        color = str(payload.get("color", item.color)).strip()
        if not name or not re.fullmatch(r"#[0-9A-Fa-f]{6}", color): return JsonResponse({"error": "Enter a valid name and colour."}, status=400)
        merge_id = str(payload.get("mergeInto", "")).strip()
        with transaction.atomic():
            if merge_id:
                target = get_object_or_404(ActivitySubcommittee, pk=merge_id, main_committee=item.main_committee)
                item.tasks.update(subcommittee=target)
                item.delete()
                return JsonResponse({"merged": True, "subcommittee": subcommittee_json(target)})
            item.name, item.color = name, color
            item.save()
        return JsonResponse({"subcommittee": subcommittee_json(item)})
    except (json.JSONDecodeError, IntegrityError):
        return JsonResponse({"error": "The subcommittee could not be updated."}, status=400)

@csrf_exempt
@require_POST
def upload_activity_file(request, task_id):
    denied = admin_required(request)
    if denied: return denied
    task = get_object_or_404(ActivityTask, pk=task_id)
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    error = validate_library_upload(uploaded)
    if error: return error
    try:
        item = ActivityAttachment.objects.create(task=task, file=uploaded, original_name=uploaded.name, mime_type=uploaded.content_type, size_bytes=uploaded.size)
        return JsonResponse({"file": activity_attachment_json(item)}, status=201)
    except Exception:
        logger.exception("activity_file_create_failed task_id=%s", task_id)
        return JsonResponse({"error": "The file could not be saved."}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_activity_file(request, attachment_id):
    denied = admin_required(request)
    if denied: return denied
    item = get_object_or_404(ActivityAttachment, pk=attachment_id)
    storage, path = item.file.storage, item.file.name
    with transaction.atomic():
        item.delete()
        transaction.on_commit(lambda: storage.delete(path))
    return JsonResponse({"deleted": True})

@require_GET
def download_activity_file(request, attachment_id):
    item = get_object_or_404(ActivityAttachment, pk=attachment_id)
    try:
        return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.original_name, content_type=item.mime_type)
    except (FileNotFoundError, OSError):
        return JsonResponse({"error": "The stored file is unavailable."}, status=404)
