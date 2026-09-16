from django.db import migrations, models


OKO_GROUPS = {
    "Tributes": "#7059A6",
    "Church Service": "#697B3E",
    "Flyers and Circulation": "#536FB5",
    "Livestream and Pictures": "#6858A8",
    "Formal Announcements": "#4F6B8A",
    "Needs Classification": "#8A8F98",
}

TASK_GROUPS = {
    "oko-01": "Tributes",
    "oko-02": "Tributes",
    "oko-03": "Tributes",
    "oko-04": "Tributes",
    "oko-05": "Church Service",
    "oko-06": "Flyers and Circulation",
    "oko-07": "Livestream and Pictures",
    "oko-08": "Flyers and Circulation",
    "oko-09": "Livestream and Pictures",
    "oko-10": "Formal Announcements",
    "oko-11": "Flyers and Circulation",
    "oko-12": "Needs Classification",
}

FUNERAL_GROUPS = {
    "oko-01": "Invitations and Letters",
    "oko-02": "Invitations and Letters",
    "oko-03": "Invitations and Letters",
    "oko-04": "Invitations and Letters",
    "oko-05": "Clergy and Order of Service",
    "oko-06": "Communications and Publicity",
    "oko-07": "Media and Documentation",
    "oko-08": "Communications and Publicity",
    "oko-09": "Media and Documentation",
    "oko-10": "Invitations and Letters",
    "oko-11": "Communications and Publicity",
    "oko-12": "Needs Classification",
}


def move_oko_tasks(apps, schema_editor):
    Subcommittee = apps.get_model("hub", "ActivitySubcommittee")
    Task = apps.get_model("hub", "ActivityTask")
    groups = {}
    for name, color in OKO_GROUPS.items():
        groups[name], _ = Subcommittee.objects.get_or_create(
            main_committee="oko", name=name, defaults={"color": color}
        )
    for source_key, group_name in TASK_GROUPS.items():
        Task.objects.filter(source_key=source_key).update(
            main_committee="oko", subcommittee=groups[group_name]
        )


def restore_funeral_tasks(apps, schema_editor):
    Subcommittee = apps.get_model("hub", "ActivitySubcommittee")
    Task = apps.get_model("hub", "ActivityTask")
    for source_key, group_name in FUNERAL_GROUPS.items():
        group = Subcommittee.objects.filter(main_committee="funeral", name=group_name).first()
        Task.objects.filter(source_key=source_key).update(
            main_committee="funeral", subcommittee=group
        )
    Subcommittee.objects.filter(main_committee="oko").delete()


class Migration(migrations.Migration):
    dependencies = [("hub", "0005_activity_management")]

    operations = [
        migrations.AlterField(
            model_name="activitysubcommittee",
            name="main_committee",
            field=models.CharField(
                choices=[
                    ("funeral", "Funeral Committee"),
                    ("brochure", "Brochure Committee"),
                    ("oko", "Logistics Uncle Oko"),
                ],
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="activitytask",
            name="main_committee",
            field=models.CharField(
                choices=[
                    ("funeral", "Funeral Committee"),
                    ("brochure", "Brochure Committee"),
                    ("oko", "Logistics Uncle Oko"),
                ],
                max_length=16,
            ),
        ),
        migrations.RunPython(move_oko_tasks, restore_funeral_tasks),
    ]
