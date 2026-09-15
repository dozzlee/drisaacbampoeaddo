import json
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .models import TributeAttachment, UserProfile, normalize_phone

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

@require_GET
def tribute_files(request):
    records = {}
    for item in TributeAttachment.objects.all(): records.setdefault(str(item.party_id), []).append(attachment_json(item))
    return JsonResponse(records)

@csrf_exempt
@require_POST
def upload_tribute_file(request, party_id):
    uploaded = request.FILES.get("file")
    if not uploaded: return JsonResponse({"error": "Choose a file to upload."}, status=400)
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if uploaded.content_type not in allowed: return JsonResponse({"error": "This file type is not supported."}, status=400)
    if uploaded.size > 10 * 1024 * 1024: return JsonResponse({"error": "Files must be smaller than 10 MB."}, status=413)
    item = TributeAttachment.objects.create(party_id=party_id, file=uploaded, original_name=uploaded.name, mime_type=uploaded.content_type, size_bytes=uploaded.size)
    return JsonResponse(attachment_json(item), status=201)

@require_GET
def download_tribute_file(request, attachment_id):
    item = get_object_or_404(TributeAttachment, pk=attachment_id)
    return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.original_name, content_type=item.mime_type)
