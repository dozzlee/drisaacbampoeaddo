import uuid
from django.db import migrations, models
import django.db.models.deletion


FUNERAL_SUBCOMMITTEES = [
    ("Venue and Grounds", "#4F7CAC"), ("Catering", "#B7791F"), ("Protocol", "#7357A3"),
    ("Security and Traffic", "#496A5C"), ("Transport and Logistics", "#39798D"),
    ("Medical and First Aid", "#A64B5C"), ("Finance and Budgeting", "#8A6D3B"),
    ("Communications and Publicity", "#536FB5"), ("Media and Documentation", "#6858A8"),
    ("Entertainment", "#A65E72"), ("Clergy and Order of Service", "#697B3E"),
    ("Ushers and Guest Services", "#3F7D72"), ("Accommodation", "#7B6D8D"),
    ("Family Coordination", "#9A5B4F"), ("Donations and Welfare", "#477A65"),
    ("Invitations and Letters", "#4F6B8A"), ("Technical and Sound", "#596675"),
    ("Burial and Cemetery", "#6A625C"), ("Thanksgiving Service", "#7B7048"),
    ("Cloth and Branding", "#8A5570"), ("General Administration", "#667784"),
    ("Needs Classification", "#8A8F98"),
]

BROCHURE_SUBCOMMITTEES = [
    ("Tribute Committee", "#7059A6"), ("Editorial and Writing", "#3F6F8F"),
    ("Photography and Images", "#6A5DAA"), ("Design and Layout", "#9B5D75"),
    ("Printing and Production", "#7A653D"), ("Invitations and Letters", "#4F6B8A"),
    ("Biography and Family History", "#8B5D4C"), ("Proofreading and Approval", "#4F7A68"),
    ("Distribution", "#527A82"), ("Communications", "#536FB5"),
    ("Media and Documentation", "#6858A8"), ("Needs Classification", "#8A8F98"),
]

EXISTING_TASKS = [
    (1,"Dispatch call-for-tribute letters using the CLOGSAG protocol list","brochure","Tribute Committee","CLOGSAG National Secretariat","2026-09-09","Urgent","completed",100,"Confirm who will prepare each tribute."),
    (2,"Produce the CLOGSAG tribute list","brochure","Tribute Committee","CLOGSAG National Secretariat","2026-09-09","Urgent","completed",100,"Decision required on tribute contributors."),
    (3,"Prepare and dispatch two Winners Chapel letters","funeral","Invitations and Letters","To be assigned","2026-09-09","High","completed",100,"Include church personalities from Ghana and Nigeria."),
    (4,"Prepare Accra Academy invitation list and hand it to Theo","funeral","Invitations and Letters","Angelo","2026-09-09","High","completed",100,"Personal invitation workstream."),
    (5,"Finalise the family visitation letter list","funeral","Invitations and Letters","To be assigned","2026-09-10","Urgent","completed",100,"List required for family letters."),
    (6,"Submit completed letters to CLOGSAG for dispatch","brochure","Tribute Committee","To be assigned","2026-09-10","Urgent","completed",100,"Include proof of dispatch."),
    (7,"Prepare the final list for family letters","funeral","Invitations and Letters","To be assigned","2026-09-12","High","completed",100,"Check names and titles."),
    (8,"Collect biography, family information, photographs and funeral details","brochure","Biography and Family History","Editorial Team","2026-09-15","High","in-progress",50,"Content Collection I."),
    (9,"Collect officiating clergy, ministers and church information","funeral","Clergy and Order of Service","Church-Related Subcommittee","2026-09-19","High","in-progress",50,"Content Collection II."),
    (10,"Confirm Pre-Burial, Burial, Thanksgiving and Graveside service details","funeral","Clergy and Order of Service","Burial and Thanksgiving Subcommittee","2026-09-24","Urgent","not-started",0,"Private burial information must stay restricted."),
    (11,"Receive all stakeholder tributes","brochure","Tribute Committee","Tribute Team","2026-09-24","Urgent","in-progress",50,"Follow up with all outstanding organisations."),
    (12,"Collect and compile hymns, songs and lyrics","brochure","Editorial and Writing","Editing Subcommittee","2026-09-29","High","not-started",0,"Confirm correct sequence and wording."),
    (13,"Populate the first brochure draft","brochure","Design and Layout","Editorial and Design Teams","2026-10-02","Urgent","not-started",0,"Use all approved content received."),
    (14,"Review layout, biography, photographs, clergy, tributes and Order of Service","brochure","Proofreading and Approval","Funeral Central Coordination Team","2026-10-05","High","not-started",0,"First formal review."),
    (15,"Complete corrections and collect outstanding content","brochure","Editorial and Writing","Editorial Team","2026-10-08","High","not-started",0,"Apply first review comments."),
    (16,"Final review and proofreading","brochure","Proofreading and Approval","Editing Subcommittee","2026-10-09","Urgent","not-started",0,"Check names, titles, dates, spelling, sequence, photographs and lyrics."),
    (17,"Obtain final approval of the complete brochure","brochure","Proofreading and Approval","Funeral Central Coordination Team","2026-10-12","Urgent","not-started",0,"Record approval and final version."),
    (18,"Complete final artwork and pre-print checks","brochure","Design and Layout","Design Team","2026-10-14","Urgent","not-started",0,"Submit approved artwork to printer."),
    (19,"Print the final funeral brochure","brochure","Printing and Production","To be assigned","2026-10-15","Urgent","not-started",0,"Only the approved version may be printed."),
    (20,"Approve the official photograph, catchphrase and watermark","funeral","Communications and Publicity","Communications and Design Teams","2026-09-18","High","in-progress",50,"Publish approved assets for all media partners."),
    (21,"Coordinate documentary and memorial website updates","funeral","Media and Documentation","Documentary and Communications Teams","2026-10-15","Normal","in-progress",50,"Use approved funeral content only."),
    (22,"Plan first aid, ambulance and paramedic support","funeral","Medical and First Aid","To be assigned","2026-10-23","High","not-started",0,"Coverage required for funeral events."),
    (23,"Define the donations collection and accountability process","funeral","Donations and Welfare","To be assigned","2026-10-16","High","not-started",0,"Name the responsible people."),
    (24,"Coordinate distribution of the funeral cloth","funeral","Cloth and Branding","Genevieve","2026-10-23","Normal","not-started",0,"Confirm collection and distribution plan."),
    (25,"Prepare the funeral event layout","funeral","Venue and Grounds","Protocol Team","2026-10-23","High","not-started",0,"Account for the private burial arrangement."),
]

NEW_TASKS = [
    ("pdf-01","Report letterhead status and complete obituary design","funeral","Communications and Publicity","Communications Team","2026-09-09","Urgent","awaiting-feedback","Letterhead target was 7 September. Obituary design target is 9 September with placeholder text where needed."),
    ("pdf-02","Consolidate responsibilities, costs, owners and delivery dates","funeral","General Administration","Funeral organiser, Communications Team and CLOGSAG",None,"Urgent","not-started","Circulate one consolidated contact list."),
    ("pdf-03","Obtain family and church decisions for service running orders","funeral","Family Coordination","Family, pastor and Seth",None,"High","awaiting-feedback","Settle gathering format, viewing, traditional rites, service roles and timing."),
    ("pdf-04","Approve content direction and begin invitation planning","funeral","Communications and Publicity","Communications and Tribute Teams",None,"High","in-progress","Approve photo and catchphrase and allocate content deadlines."),
    ("pdf-05","Confirm family decisions on gathering, rites and private burial delegation","funeral","Family Coordination","Family",None,"Urgent","awaiting-feedback","Include speakers, songs, viewing, route and photography restrictions."),
    ("pdf-06","Provide guest lists and VIP details","funeral","Protocol","Family and CLOGSAG","2026-11-04","High","not-started","Confirm the date inconsistency noted in the minutes before circulation."),
    ("pdf-07","Prepare draft running orders, layouts, procurement list and costs","funeral","General Administration","Seth / organiser",None,"High","not-started","Identify who remains at the venue during private burial."),
    ("pdf-08","Confirm church roles, service order, speakers and thanksgiving arrangements","funeral","Clergy and Order of Service","Church / pastor",None,"Urgent","awaiting-feedback","Discuss proposed libation and traditional rites with the family."),
    ("pdf-09","Coordinate protocol and funeral cloth arrangements","funeral","Cloth and Branding","PRO team / Genevieve",None,"High","in-progress","Include government and civil service protocol and Jamma follow-up."),
    ("pdf-10","Set owners and dates for documentary, website and brochure delivery","funeral","Media and Documentation","Communications Team",None,"High","in-progress","Align obituary wording with the family decision."),
    ("pdf-11","Confirm Tribute Team membership and curate contributions","brochure","Tribute Committee","Separate Tribute Team","2026-09-24","Urgent","in-progress","Allocate speakers, slots, durations and vigil tributes."),
    ("pdf-12","Plan institutional invitation visits","funeral","Invitations and Letters","Invitation delegation",None,"High","not-started","Agree visitors, dates, cards, drinks and messages for each institution."),
    ("pdf-13","Prepare donation collection and accountability plan","funeral","Donations and Welfare","Banking partners",None,"High","not-started","Include staffing and support for participating groups."),
    ("pdf-14","Return named contacts, deliverables, costs and completion dates","funeral","General Administration","All appointed leads",None,"Urgent","not-started","Report dependencies and decisions still required."),
    ("pdf-15","Conduct CLOGSAG and State House site visits","funeral","Venue and Grounds","CLOGSAG / Seth / venue teams",None,"Urgent","not-started","Verify capacity, seating, catering, viewing, tent, staging, lighting and projectors."),
    ("pdf-16","Obtain catering proposals and finalise service plan","funeral","Catering","Seth / caterers",None,"High","not-started","Obtain 4-5 proposals and confirm menus, numbers, water, waiters and distribution."),
    ("pdf-17","Confirm bands, choirs, DJ and cultural troupe","funeral","Entertainment","Entertainment / PRO",None,"High","not-started","Confirm availability, set lists, slots and technical needs."),
    ("pdf-18","Confirm Jamma songs, performance slots and movement","funeral","Entertainment","PRO / Jamma group",None,"High","not-started","Coordinate with body transport and security."),
    ("pdf-19","Confirm sound, power, lighting, projectors, toilets and vigil supplies","funeral","Technical and Sound","Seth / technical suppliers",None,"Urgent","not-started","Include backup generator, water, candles and residence supplies."),
    ("pdf-20","Finalise security, restricted photography and parking plans","funeral","Security and Traffic","Security / parking liaison",None,"Urgent","not-started","Cover vigil, residence and Accra Academy reception parking."),
    ("pdf-21","Request AMA road-use clearance and confirm residence overflow plan","funeral","Security and Traffic","Haleem",None,"Urgent","not-started","Share conditions with family, Seth and security."),
    ("pdf-22","Confirm pallbearers, body transport, route and procession","funeral","Transport and Logistics","Funeral provider / family",None,"Urgent","not-started","Set rites early enough for proposed departure from home by 7:00 a.m."),
    ("pdf-23","Confirm medical coverage and emergency response plan","funeral","Medical and First Aid","Medical provider / organiser",None,"Urgent","not-started","Share emergency contacts and nearest suitable facility."),
    ("pdf-24","Validate Accra Academy reception capacity and layout","funeral","Venue and Grounds","Accra Academy / Seth",None,"High","not-started","Plan for 2,000 guests with provision for 2,500 at 11:30 a.m."),
    ("oko-01","Collect Ministry of Agriculture tribute","funeral","Invitations and Letters","Minadi",None,"High","not-started","Logistics Uncle Oko tribute follow-up."),
    ("oko-02","Collect Accra Academy tribute","funeral","Invitations and Letters","Dr Latt",None,"High","not-started","Logistics Uncle Oko tribute follow-up."),
    ("oko-03","Collect New Hope School tribute","funeral","Invitations and Letters","Alhaji",None,"High","not-started","Logistics Uncle Oko tribute follow-up."),
    ("oko-04","Collect KNUST Katanga tribute","funeral","Invitations and Letters","Alhaji",None,"High","not-started","Logistics Uncle Oko tribute follow-up."),
    ("oko-05","Confirm church service date and time before flyer design","funeral","Clergy and Order of Service","To be confirmed",None,"Urgent","awaiting-feedback","Notes mention changing the time to 9 and also record 6:30. Resolve before issuing flyers."),
    ("oko-06","Prepare church service flyers in the agreed format","funeral","Communications and Publicity","To be assigned",None,"High","blocked","Begin after the service date and time are confirmed."),
    ("oko-07","Arrange CLOGSAG livestream for the church service","funeral","Media and Documentation","CLOGSAG",None,"High","not-started","Confirm platform, technical lead and broadcast time."),
    ("oko-08","Circulate church service information to listed groups","funeral","Communications and Publicity","Team Bampoeaddo",None,"High","not-started","Include Aunty Borley, Accra Academy, Angelo, Uncle Nii Darko, CLOGSAG and Alhaji."),
    ("oko-09","Collect SRID pictures for the church service","funeral","Media and Documentation","SRID","2026-09-17","High","not-started","Thursday deadline from the logistics notes."),
    ("oko-10","Send formal announcement letter to Ministry of Agriculture","funeral","Invitations and Letters","Sena",None,"High","not-started","Sena to coordinate the Ministry item."),
    ("oko-11","Create visiting schedule flyer for Wednesday to Saturday","funeral","Communications and Publicity","To be assigned",None,"High","not-started","Include Ministry of Agriculture on Thursday. Wednesday details still require confirmation."),
    ("oko-12","Clarify remaining Wednesday visit details","funeral","Needs Classification","To be confirmed",None,"Normal","awaiting-feedback","The source note ends at Wednesday without a destination or owner."),
]


def seed_activities(apps, schema_editor):
    Subcommittee = apps.get_model("hub", "ActivitySubcommittee")
    Task = apps.get_model("hub", "ActivityTask")
    lookup = {}
    for main, records in (("funeral", FUNERAL_SUBCOMMITTEES), ("brochure", BROCHURE_SUBCOMMITTEES)):
        for name, color in records:
            item, _ = Subcommittee.objects.get_or_create(main_committee=main, name=name, defaults={"color": color})
            lookup[(main, name)] = item
    for task_id, title, main, sub, owner, deadline, priority, status, progress, notes in EXISTING_TASKS:
        Task.objects.get_or_create(source_key=f"legacy-{task_id}", defaults={"title": title, "main_committee": main, "subcommittee": lookup[(main, sub)], "owner": owner, "deadline": deadline, "priority": priority, "status": status, "progress": progress, "notes": notes})
    for source_key, title, main, sub, owner, deadline, priority, status, notes in NEW_TASKS:
        Task.objects.get_or_create(source_key=source_key, defaults={"title": title, "main_committee": main, "subcommittee": lookup[(main, sub)], "owner": owner, "deadline": deadline, "priority": priority, "status": status, "progress": 0, "notes": notes})


class Migration(migrations.Migration):
    dependencies = [("hub", "0004_mediaasset")]
    operations = [
        migrations.CreateModel(name="ActivitySubcommittee", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("main_committee", models.CharField(choices=[("funeral", "Funeral Committee"), ("brochure", "Brochure Committee")], max_length=16)),
            ("name", models.CharField(max_length=160)), ("color", models.CharField(default="#5679C8", max_length=7)),
            ("active", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering": ["main_committee", "name"], "constraints": [models.UniqueConstraint(fields=("main_committee", "name"), name="unique_activity_subcommittee")]}),
        migrations.CreateModel(name="ActivityTask", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=500)), ("main_committee", models.CharField(choices=[("funeral", "Funeral Committee"), ("brochure", "Brochure Committee")], max_length=16)),
            ("owner", models.CharField(blank=True, max_length=255)), ("supporting_members", models.JSONField(blank=True, default=list)),
            ("start_date", models.DateField(blank=True, null=True)), ("deadline", models.DateField(blank=True, null=True)),
            ("priority", models.CharField(default="Normal", max_length=20)),
            ("status", models.CharField(choices=[("not-started", "Not Started"), ("in-progress", "In Progress"), ("awaiting-feedback", "Awaiting Feedback"), ("blocked", "Blocked"), ("nearing-completion", "Nearing Completion"), ("completed", "Completed"), ("overdue", "Overdue")], default="not-started", max_length=32)),
            ("progress", models.PositiveSmallIntegerField(default=0)), ("notes", models.TextField(blank=True)), ("labels", models.JSONField(blank=True, default=list)),
            ("source_key", models.CharField(blank=True, max_length=120, null=True, unique=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("subcommittee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks", to="hub.activitysubcommittee")),
        ], options={"ordering": ["deadline", "id"]}),
        migrations.CreateModel(name="ActivityAttachment", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("file", models.FileField(upload_to="activities/%Y/%m/")), ("original_name", models.CharField(max_length=255)),
            ("mime_type", models.CharField(max_length=160)), ("size_bytes", models.PositiveBigIntegerField()), ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="hub.activitytask")),
        ], options={"ordering": ["uploaded_at"]}),
        migrations.RunPython(seed_activities, migrations.RunPython.noop),
    ]
