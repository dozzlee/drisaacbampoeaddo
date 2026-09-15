import json
import logging
import re
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.http import FileResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .models import ActivityAttachment, ActivitySubcommittee, ActivityTask, MediaAsset, TributeAttachment, TributeParty, UserProfile, normalize_phone

logger = logging.getLogger(__name__)

def user_json(user): return {"id": str(user.id), "name": user.full_name, "phone": user.phone, "role": user.role}

@require_GET
def health(request):
    try:
        with connection.cursor() as cursor: cursor.execute("SELECT 1"); cursor.fetchone()
        return JsonResponse({"status": "ok", "database": "postgresql"})
    except Exception: return JsonResponse({"status": "error", "database": "unavailable"}, status=503)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def users(request):
    if request.method == "GET": return JsonResponse({"users": [user_json(user) for user in UserProfile.objects.order_by("full_name")]})
    try:
        payload = json.loads(request.body)
        normalized = normalize_phone(payload.get("phone"))
        existing = UserProfile.objects.filter(normalized_phone=normalized).first()
        if existing: return JsonResponse({"user": user_json(existing), "created": False})
        user = UserProfile.objects.create(full_name=payload.get("name", "").strip(), phone=payload.get("phone", "").strip(), role=payload.get("role", UserProfile.Role.USER))
        return JsonResponse({"user": user_json(user), "created": True}, status=201)
    except (ValidationError, ValueError, KeyError) as error: return JsonResponse({"error": str(error)}, status=400)
    except IntegrityError: return JsonResponse({"error": "This phone number already belongs to a user."}, status=409)

def attachment_json(item):
    return {"id": str(item.id), "name": item.original_name, "href": f"/api/tributes/files/{item.id}/download", "size": item.size_bytes, "uploadedAt": item.uploaded_at.isoformat()}

ALLOWED_TRIBUTE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

def validate_tribute_upload(uploaded):
    if uploaded.content_type not in ALLOWED_TRIBUTE_TYPES:
        return JsonResponse({"error": "This file type is not supported."}, status=400)
    if uploaded.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "Files must be smaller than 10 MB."}, status=413)
    return None

def party_json(party):
    return {"id": party.id, "name": party.name, "phone": party.phone, "request": party.request_status, "tribute": party.tribute_status}

@csrf_exempt
@require_http_methods(["GET", "POST"])
def tribute_parties(request):
    if request.method == "GET":
        return JsonResponse({"parties": [party_json(party) for party in TributeParty.objects.all()]})
    try:
        payload = json.loads(request.body)
        name = str(payload.get("name", "")).strip()
        phone = str(payload.get("phone", "")).strip()
        if not name:
            return JsonResponse({"error": "Person or organisation is required."}, status=400)
        party = TributeParty.objects.create(name=name, phone=phone)
        logger.info("tribute_party_created id=%s", party.id)
        return JsonResponse({"party": party_json(party)}, status=201)
    except (json.JSONDecodeError, TypeError, ValueError):
        logger.warning("tribute_party_create_invalid_payload")
        return JsonResponse({"error": "Invalid party data."}, status=400)

@require_GET
def tribute_files(request):
    records = {}
    for item in TributeAttachment.objects.all(): records.setdefault(str(item.party_id), []).append(attachment_json(item))
    return JsonResponse(records)

@csrf_exempt
@require_POST
def upload_tribute_file(request, party_id):
    if not TributeParty.objects.filter(pk=party_id).exists():
        return JsonResponse({"error": "Tribute party not found."}, status=404)
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    validation_error = validate_tribute_upload(uploaded)
    if validation_error: return validation_error
    try:
        with transaction.atomic():
            item = TributeAttachment.objects.create(party_id=party_id, file=uploaded, original_name=uploaded.name, mime_type=uploaded.content_type, size_bytes=uploaded.size)
        logger.info("tribute_file_created id=%s party_id=%s size=%s", item.id, party_id, uploaded.size)
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
    if not new_name and not replacement:
        return JsonResponse({"error": "Enter a file name or choose a replacement file."}, status=400)
    if replacement:
        validation_error = validate_tribute_upload(replacement)
        if validation_error: return validation_error
    old_storage = item.file.storage
    old_path = item.file.name
    try:
        with transaction.atomic():
            if replacement:
                item.file = replacement
                item.mime_type = replacement.content_type
                item.size_bytes = replacement.size
            item.original_name = new_name or replacement.name
            item.save()
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
    try:
        with transaction.atomic():
            item.delete()
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

ALLOWED_LIBRARY_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml",
    "video/mp4", "video/quicktime", "video/webm", "audio/mpeg", "audio/wav", "audio/mp4",
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain", "text/csv",
}

def request_role(request):
    return request.headers.get("X-Teams-Role", "user").lower()

def admin_required(request):
    if request_role(request) != "admin":
        return JsonResponse({"error": "Administrator access is required."}, status=403)
    return None

def validate_library_upload(uploaded):
    if uploaded.content_type not in ALLOWED_LIBRARY_TYPES:
        return JsonResponse({"error": "This media or document type is not supported."}, status=400)
    if uploaded.size > 100 * 1024 * 1024:
        return JsonResponse({"error": "Files must be smaller than 100 MB."}, status=413)
    return None

def media_asset_json(item):
    has_file = bool(item.file)
    preview_href = f"/api/media/{item.id}/preview" if has_file else item.external_url
    download_href = f"/api/media/{item.id}/download" if has_file else item.external_url
    return {
        "id": str(item.id), "title": item.title, "assetType": item.asset_type,
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
        records = MediaAsset.objects.all()
        if request_role(request) == "media":
            records = records.filter(available_to_media=True).exclude(document_status=MediaAsset.Status.ARCHIVED)
        return JsonResponse({"items": [media_asset_json(item) for item in records]})
    denied = admin_required(request)
    if denied: return denied
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    upload_error = validate_library_upload(uploaded)
    if upload_error: return upload_error
    item = MediaAsset(original_name=uploaded.name, mime_type=uploaded.content_type, size_bytes=uploaded.size)
    apply_media_fields(item, request.POST)
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
            return FileResponse(item.file.open("rb"), as_attachment=attachment, filename=item.original_name, content_type=item.mime_type)
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
