# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError
from django_pgjsonb import JSONField
import logging


from core.fb_api_wrapper import Messenger, FacebookException

logger = logging.getLogger()


def json_default():
    return {}

class AppUser(models.Model):
    ref_id = models.CharField(max_length=100, blank=False, null=False, unique=True)
    email = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)

    custom_data = JSONField(null=False, blank=False, default=json_default, db_index=True)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)


    @staticmethod
    def setup(ref_id):

        try:
            user = AppUser.objects.get(ref_id=ref_id)
            return user

        except ObjectDoesNotExist:
            user = AppUser()

        user.ref_id = ref_id

        #get fb profile data
        try:
            m = Messenger(settings.FB_MESSENGER_TOKEN)
            profile = m.get_profile(ref_id)
        except FacebookException:
            profile = None

        if profile:

            user.first_name = profile.get('first_name', None)
            user.last_name = profile.get('last_name', None)
            user.custom_data['facebook_data'] = profile

        try:
            user.save()

        except IntegrityError,inst:
            #race condition
            logger.error("DB Error:" % inst)
            return AppUser.objects.get(ref_id=ref_id)

        return user

    def add_child(self, first_name, phone_number):

        child = Child()

        if not first_name:
            first_name = "Child"

        child.user = self
        child.first_name = first_name
        child.phone_number = phone_number

        child.save()

class Child(models.Model):

    user = models.ForeignKey(AppUser, null=False, blank=False, related_name="children")

    first_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=200, blank=True, null=True)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)


class Reminder(models.Model):

    child = models.ForeignKey(Child, null=False, blank=False, related_name="reminders")

    KIND_CHOICES = (
        (100, 'Ready By'),
        (200, 'Chore'),
        (300, 'Curfew'),
    )
    kind = models.IntegerField(choices = KIND_CHOICES, blank=False, null=False)

    at_time = models.TimeField(blank=False, null=False)

    on_mon = models.BooleanField(default=False, null=False)
    on_tue = models.BooleanField(default=False, null=False)
    on_wed = models.BooleanField(default=False, null=False)
    on_thu = models.BooleanField(default=False, null=False)
    on_fri = models.BooleanField(default=False, null=False)
    on_sat = models.BooleanField(default=False, null=False)
    on_sun = models.BooleanField(default=False, null=False)

    active = models.BooleanField(default=True, null=False)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)


