# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class AppUser(models.Model):
    ref_id = models.CharField(max_length=100, blank=False, null=False, unique=True)
    email = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=200, blank=True, null=True, db_index=True)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)
