# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-25 09:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('youngsphere_sites', '0003_auto_20190121_0707'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userminiprofile',
            old_name='Phone_no',
            new_name='contact_number',
        ),
        migrations.AddField(
            model_name='userminiprofile',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='youngsphere_sites.School'),
        ),
    ]
