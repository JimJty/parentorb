# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-09 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_action_was_parent_notified'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='nick_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]