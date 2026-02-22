"""
Add UUID field to DataspaceUser.

This migration safely adds a UUID field to existing rows by:
1. Adding the field as nullable (no unique constraint yet)
2. Populating a UUID for every existing row
3. Making the field non-nullable and unique
"""

import uuid

from django.db import migrations, models


def populate_uuids(apps, schema_editor):
    DataspaceUser = apps.get_model("onboard", "DataspaceUser")
    for user in DataspaceUser.objects.all():
        user.uuid = uuid.uuid4()
        user.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("onboard", "0002_alter_dataspaceuser_id"),
    ]

    operations = [
        # Step 1: Add nullable UUID field (no unique constraint yet)
        migrations.AddField(
            model_name="dataspaceuser",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        # Step 2: Populate UUIDs for existing rows
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        # Step 3: Make non-nullable, unique, and non-editable
        migrations.AlterField(
            model_name="dataspaceuser",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
