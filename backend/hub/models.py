import re
import uuid
from django.core.exceptions import ValidationError
from django.db import models

def normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("00"): digits = digits[2:]
    if digits.startswith("0") and len(digits) == 10: digits = "233" + digits[1:]
    if len(digits) < 9 or len(digits) > 15: raise ValidationError("Enter a valid phone number.")
    return digits

class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "Normal user"
        MEDIA = "media", "Media person"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32)
    normalized_phone = models.CharField(max_length=15, unique=True, editable=False)
    role = models.CharField(max_length=10, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        self.normalized_phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

class TributeParty(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    request_status = models.CharField(max_length=32, default="Not recorded")
    tribute_status = models.CharField(max_length=32, default="Not recorded")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

class TributeAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    party_id = models.PositiveBigIntegerField(db_index=True)
    file = models.FileField(upload_to="tributes/%Y/%m/")
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["uploaded_at"]
