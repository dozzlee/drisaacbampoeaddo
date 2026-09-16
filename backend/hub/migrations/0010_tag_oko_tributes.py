from django.db import migrations, models


OKO_TRIBUTES = {
    "Ministry of Agriculture": "Minadi",
    "Accra Academy": "Dr Latt",
    "New Hope School": "Alhagi",
    "KNUST Katanga": "Alhagi",
}


def tag_oko_tributes(apps, schema_editor):
    TributeParty = apps.get_model("hub", "TributeParty")
    ActivityTask = apps.get_model("hub", "ActivityTask")
    for name, assigned_to in OKO_TRIBUTES.items():
        party, _ = TributeParty.objects.get_or_create(name=name)
        party.main_committee = "oko"
        party.assigned_to = assigned_to
        party.save(update_fields=["main_committee", "assigned_to"])
    ActivityTask.objects.filter(source_key__in=["oko-03", "oko-04"]).update(owner="Alhagi")


class Migration(migrations.Migration):
    dependencies = [("hub", "0009_add_oko_tribute_parties")]

    operations = [
        migrations.AddField(
            model_name="tributeparty",
            name="main_committee",
            field=models.CharField(
                choices=[("general", "General tribute register"), ("oko", "Logistics Uncle Oko")],
                db_index=True,
                default="general",
                max_length=16,
            ),
        ),
        migrations.RunPython(tag_oko_tributes, migrations.RunPython.noop),
    ]
