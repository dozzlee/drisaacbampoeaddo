from django.db import migrations, models


PARTIES = [
    ("NDC - National Democratic Congress", ""), ("NPP - New Patriotic Party", ""),
    ("CPP - Convention People's Party", ""), ("PNC - People's National Convention", ""),
    ("Office of former President - H.E. Nana Addo Danquah Akuffo Addo", ""),
    ("Majority Leader of Parliament", ""), ("Minority Leader of Parliament", ""),
    ("The Speaker of Parliament", ""), ("CLOGSAG National Secretariat", ""),
    ("Office of the Head of the Civil Service (OHCS)", ""),
    ("Office of the Head of Local Government Service (OHLGS)", ""),
    ("TUC / Organised Labour", ""), ("FORUM for Public Sector Associations and Unions", ""),
    ("Pempamsie Hotel", ""), ("Ministry of Labour, Jobs and Employment", ""),
    ("PSI - NCC - Ghana", ""), ("PSI - Africa & Arab Countries", ""),
    ("Controller and Accountant General's Department", ""), ("CLOGSAG Ladies", ""),
    ("Hedge Pensions Trust", ""), ("Ghana National Association of Teachers (GNAT)", "0243532235"),
    ("National Association of Graduate Teachers (NAGRAT)", "0244665065"),
    ("PRETAG", "0208967598"), ("Ghana Medical Association (GMA)", "0244601688"),
    ("Ghana Registered Nurses and Midwives Association (GRNMA)", "0244654068"),
    ("Government and Hospital Pharmacists' Association (GHOSPA)", "0245434262"),
    ("Ghana Association of Certified Registered Anesthetists (GACRA)", "0266828638"),
    ("Judicial Service Staff Association of Ghana (JUSAG)", ""),
    ("Ghana Physicians Association", ""), ("Board Chairman of Accra Academy", ""),
    ("The Management & Staff of Accra Academy", ""),
    ("The General Secretary, Accra Academy Old Boys Association", ""),
    ("The General Secretary, BLEOO '85", ""),
]


def seed_parties(apps, schema_editor):
    TributeParty = apps.get_model("hub", "TributeParty")
    TributeAttachment = apps.get_model("hub", "TributeAttachment")
    for party_id, (name, phone) in enumerate(PARTIES, start=1):
        TributeParty.objects.get_or_create(id=party_id, defaults={"name": name, "phone": phone})
    # Preserve attachments uploaded against browser-generated IDs before parties became durable.
    for party_id in TributeAttachment.objects.values_list("party_id", flat=True).distinct():
        TributeParty.objects.get_or_create(
            id=party_id,
            defaults={"name": f"Recovered tribute party {party_id}", "phone": ""},
        )


class Migration(migrations.Migration):
    dependencies = [("hub", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TributeParty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("request_status", models.CharField(default="Not recorded", max_length=32)),
                ("tribute_status", models.CharField(default="Not recorded", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.RunPython(seed_parties, migrations.RunPython.noop),
        migrations.RunSQL(
            "SELECT setval(pg_get_serial_sequence('hub_tributeparty', 'id'), COALESCE(MAX(id), 1), true) FROM hub_tributeparty",
            migrations.RunSQL.noop,
        ),
    ]
