from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("hub", "0002_tributeparty")]
    operations = [
        migrations.RunSQL(
            "SELECT setval(pg_get_serial_sequence('hub_tributeparty', 'id'), COALESCE(MAX(id), 1), true) FROM hub_tributeparty",
            migrations.RunSQL.noop,
        )
    ]
