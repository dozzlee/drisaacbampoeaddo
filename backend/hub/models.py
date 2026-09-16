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
    class MainCommittee(models.TextChoices):
        GENERAL = "general", "General tribute register"
        OKO = "oko", "Logistics Uncle Oko"

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    assigned_to = models.CharField(max_length=255, blank=True)
    main_committee = models.CharField(max_length=16, choices=MainCommittee.choices, default=MainCommittee.GENERAL, db_index=True)
    request_status = models.CharField(max_length=32, default="Not recorded")
    tribute_status = models.CharField(max_length=32, default="Not recorded")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name

class TributeAttachment(models.Model):
    class AttachmentType(models.TextChoices):
        FILE = "file", "Supporting file"
        TRIBUTE = "tribute", "Tribute"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    party_id = models.PositiveBigIntegerField(db_index=True)
    attachment_type = models.CharField(max_length=12, choices=AttachmentType.choices, default=AttachmentType.FILE, db_index=True)
    file = models.FileField(upload_to="tributes/%Y/%m/")
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["uploaded_at"]

class MediaAsset(models.Model):
    class AssetType(models.TextChoices):
        MEDIA = "media", "Media"
        DOCUMENT = "document", "Document"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "Under review"
        APPROVED = "approved", "Approved"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=12, choices=AssetType.choices)
    category = models.CharField(max_length=160)
    description = models.TextField()
    file = models.FileField(upload_to="library/%Y/%m/", blank=True)
    external_url = models.CharField(max_length=500, blank=True)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=160)
    size_bytes = models.PositiveBigIntegerField(default=0)
    labels = models.JSONField(default=list, blank=True)
    date_created = models.DateField(null=True, blank=True)
    event_activity = models.CharField(max_length=160, blank=True)
    responsible_committee = models.CharField(max_length=160, blank=True)
    uploaded_by_name = models.CharField(max_length=160, blank=True)
    owner_contact = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    confidentiality = models.CharField(max_length=80, default="Internal")
    version = models.CharField(max_length=40, default="1.0")
    document_status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    available_to_media = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title

class ActivitySubcommittee(models.Model):
    class MainCommittee(models.TextChoices):
        FUNERAL = "funeral", "Funeral Committee"
        BROCHURE = "brochure", "Brochure Committee"
        OKO = "oko", "Logistics Uncle Oko"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    main_committee = models.CharField(max_length=16, choices=MainCommittee.choices)
    name = models.CharField(max_length=160)
    color = models.CharField(max_length=7, default="#5679C8")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["main_committee", "name"]
        constraints = [models.UniqueConstraint(fields=["main_committee", "name"], name="unique_activity_subcommittee")]

    def __str__(self):
        return f"{self.get_main_committee_display()} - {self.name}"

class ActivityTask(models.Model):
    class MainCommittee(models.TextChoices):
        FUNERAL = "funeral", "Funeral Committee"
        BROCHURE = "brochure", "Brochure Committee"
        OKO = "oko", "Logistics Uncle Oko"

    class Status(models.TextChoices):
        NOT_STARTED = "not-started", "Not Started"
        IN_PROGRESS = "in-progress", "In Progress"
        AWAITING_FEEDBACK = "awaiting-feedback", "Awaiting Feedback"
        BLOCKED = "blocked", "Blocked"
        NEARING_COMPLETION = "nearing-completion", "Nearing Completion"
        COMPLETED = "completed", "Completed"
        OVERDUE = "overdue", "Overdue"

    title = models.CharField(max_length=500)
    main_committee = models.CharField(max_length=16, choices=MainCommittee.choices)
    subcommittee = models.ForeignKey(ActivitySubcommittee, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    owner = models.CharField(max_length=255, blank=True)
    supporting_members = models.JSONField(default=list, blank=True)
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, default="Normal")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NOT_STARTED)
    progress = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    labels = models.JSONField(default=list, blank=True)
    source_key = models.CharField(max_length=120, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["deadline", "id"]

    def __str__(self):
        return self.title

class ActivityAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(ActivityTask, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="activities/%Y/%m/")
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=160)
    size_bytes = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]
