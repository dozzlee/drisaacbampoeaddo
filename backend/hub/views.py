import json
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .models import TributeAttachment, TributeParty, UserProfile, normalize_phone

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

@require_GET
def download_tribute_file(request, attachment_id):
    item = get_object_or_404(TributeAttachment, pk=attachment_id)
    try:
        return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.original_name, content_type=item.mime_type)
    except (FileNotFoundError, OSError):
        logger.warning("tribute_file_missing id=%s", item.id)
        return JsonResponse({"error": "The stored file is unavailable."}, status=404)
