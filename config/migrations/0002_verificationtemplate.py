# Generated by Django 3.0.7 on 2024-04-02 08:52

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VerificationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('verificationTemplateName', models.CharField(blank=True, max_length=255, null=True)),
                ('walletName', models.CharField(blank=True, max_length=255, null=True)),
                ('walletLocation', models.CharField(blank=True, max_length=255, null=True)),
                ('issuerName', models.CharField(blank=True, max_length=255, null=True)),
                ('issuerLocation', models.CharField(blank=True, max_length=255, null=True)),
                ('issuerLogoUrl', models.CharField(blank=True, max_length=255, null=True)),
                ('dataSourceId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='config.DataSource')),
            ],
        ),
    ]
