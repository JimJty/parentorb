# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-29 03:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_reminder'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='time_offset',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
