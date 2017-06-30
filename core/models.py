# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime
import time

import pytz
from dateutil.tz import tzoffset, tzutc
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError
from django.utils import timezone
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
    time_offset = models.IntegerField(default=None, blank=True, null=True)

    custom_data = JSONField(null=False, blank=False, default=json_default, db_index=True)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)


    @staticmethod
    def setup(ref_id):

        if not ref_id:
            return None

        try:
            user = AppUser.objects.get(ref_id=ref_id)
            if user.edit_date > timezone.now() - timedelta(days=1):
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

            if profile.get('timezone',None):
                user.time_offset = profile.get('timezone')

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

        first_name = first_name.strip()

        child.user = self
        child.first_name = first_name
        child.phone_number = phone_number

        child.save()

        return child

    def get_children(self):

        children = self.children.all().order_by('first_name','id')

        return children

    def get_reminders(self):

        reminders = Reminder.objects.filter(child__user=self)

        return reminders

    def local_time(self):

        if not self.time_offset:
            return None

        local_time = timezone.now().astimezone(tzoffset(None, self.time_offset*60*60))

        return local_time

    def relevant_server_time(self, local_time_part):

        if not self.time_offset:
            return None

        try:
            time.strptime(local_time_part, '%H:%M')
        except ValueError:
            return False

        now_local_date = self.local_time().strftime("%Y-%m-%d")

        local_time = datetime.strptime(now_local_date + " " + local_time_part, "%Y-%m-%d %H:%M" )

        server_time = local_time + timedelta(hours=self.time_offset*-1)

        return pytz.utc.localize(server_time)

    def get_child_by_name(self, name):

        if not name:
            return None

        name = name.strip()

        children = self.children.filter(first_name__iexact=name)

        if children.count() == 1:
            return children[0]

        return None

    def get_child_by_id(self, child_id):

        child = self.children.filter(id=child_id)
        if child.count() == 1:
            return child[0]

        return None

    def add_reminder(self, child_id, kind, for_desc, is_repeated, choosen_date, reminder_time, days_selected):

        self.get_child_by_id(child_id)

        if not is_repeated:
            one_time = datetime.strptime("%sT%s" % (choosen_date, reminder_time), "%Y-%m-%dT%H:%M")
            one_time = self.relevant_server_time(one_time)
            days_selected = None
            reminder_time = None
        else:
            one_time = None
            days_selected = '|'.join(sorted(days_selected.split('|'))) #reorder

        reminder = Reminder()
        reminder.child_id = child_id
        reminder.kind = kind
        reminder.for_desc = for_desc
        reminder.one_time = one_time
        reminder.repeat_at_time = reminder_time
        reminder.repeat_days = days_selected
        reminder.active = True
        reminder.save()





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

    for_desc = models.CharField(max_length=100, blank=True, null=True)

    one_time = models.DateTimeField(blank=True, null=True)

    repeat_at_time = models.TimeField(blank=True, null=True)

    repeat_days = models.CharField(max_length=100, blank=True, null=True)

    active = models.BooleanField(default=True, null=False)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)


