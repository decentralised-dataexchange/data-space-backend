# Generated by Django 3.0.7 on 2024-04-05 06:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0004_auto_20240404_0725'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='verificationtemplate',
            name='dataSourceId',
        ),
        migrations.RemoveField(
            model_name='verificationtemplate',
            name='walletLocation',
        ),
        migrations.RemoveField(
            model_name='verificationtemplate',
            name='walletName',
        ),
    ]
