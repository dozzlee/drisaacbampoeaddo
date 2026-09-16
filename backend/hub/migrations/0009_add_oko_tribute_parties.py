from django.db import migrations


OKO_TRIBUTES = [
    ("Ministry of Agriculture", "Minadi"),
    ("Accra Academy", "Dr Latt"),
    ("New Hope School", "Alhagi"),
    ("KNUST Katanga", "Alhagi"),
]


def add_oko_tributes(apps, schema_editor):
    TributeParty = apps.get_model("hub", "TributeParty")
    for name, assigned_to in OKO_TRIBUTES:
        party, _ = TributeParty.objects.get_or_create(name=name)
        party.assigned_to = assigned_to
        party.save(update_fields=["assigned_to"])


class Migration(migrations.Migration):
    dependencies = [("hub", "0008_tributeparty_assigned_to")]

    operations = [migrations.RunPython(add_oko_tributes, migrations.RunPython.noop)]
