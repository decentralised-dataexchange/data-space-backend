# Generated manually for storing PDF in database

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organisation", "0007_organisation_privacydashboardurl"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="codeofconduct",
            name="pdfFile",
        ),
        migrations.AddField(
            model_name="codeofconduct",
            name="pdfContent",
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="codeofconduct",
            name="pdfFileName",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
