# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime
import time

import pytz
from dateutil.tz import tzoffset, tzutc
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError, transaction
from django.utils import timezone
from django_pgjsonb import JSONField
import logging

from twilio.rest import Client

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

        if not first_name:
            first_name = "Child"

        child = Child.get_by_phone(phone_number)
        if child:
            child.first_name = first_name
            child.save()
            return child

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

    def local_time(self, server_time=None):

        if not self.time_offset:
            return None

        if not server_time:
            server_time = timezone.now()

        local_time = server_time.astimezone(tzoffset(None, self.time_offset*60*60))

        return local_time

    def relevant_server_time(self, local_time_part, local_date_part=None):

        if not self.time_offset:
            return None

        try:
            time.strptime(local_time_part, '%H:%M')
        except ValueError:
            return None

        if not local_date_part:
            local_date_part = self.local_time().strftime("%Y-%m-%d")

        local_time = datetime.strptime(local_date_part + " " + local_time_part, "%Y-%m-%d %H:%M" )

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
            one_time =  self.relevant_server_time(reminder_time, choosen_date)
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

        with transaction.atomic():

            reminder.save()
            self.schedule_actions()

    def schedule_actions(self):

         for r in Reminder.objects.filter(child__user=self):

            if r.one_time:
                Action.schedule_for_user(self.id, r.id, r.schedule_time(r.one_time), r.one_time, )
            else:
                next_eight_days = []
                now = timezone.now()
                now_local = self.local_time()
                server_start_date = self.relevant_server_time(r.repeat_at_time.strftime("%H:%M"), now_local.strftime("%Y-%m-%d"))

                for i in range(0,8):
                    next_eight_days.append(server_start_date + timedelta(days=i))

                relevant_days = []
                relevant_days_of_week = r.repeat_days.split('|')
                days_of_week_added = {}

                for d in next_eight_days:
                    if str(d.weekday()) in relevant_days_of_week \
                        and d > now \
                        and str(d.weekday()) not in days_of_week_added.keys():
                            relevant_days.append(d)
                            days_of_week_added[str(d.weekday())] = True

                #now schedule the days
                for d in relevant_days:
                   Action.schedule_for_user(self.id, r.id, r.schedule_time(d), d)



class Child(models.Model):

    user = models.ForeignKey(AppUser, null=False, blank=False, related_name="children")

    first_name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=False, null=False, unique=True)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)

    @staticmethod
    def get_by_phone(phone):
        if not phone.startswith("+"):
            phone = "+" + phone

        children = Child.objects.filter(phone_number=phone)

        if children.count() == 0:
            return None
        else:
            return children[0]

    def get_active_reminder(self):

        actions = Action.objects.filter(reminder__child=self, status=500).order_by('event_time')

        if actions.count() > 0:
            return actions[0]
        else:
            return None


class Reminder(models.Model):

    DEFAULT_SCHEDULE_MINUTES = 15

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

    def schedule_time(self, event_time):

        return event_time - timedelta(minutes=self.DEFAULT_SCHEDULE_MINUTES)

class Action(models.Model):

    slug = models.CharField(max_length=100, blank=False, null=False, unique=True)
    reminder = models.ForeignKey(Reminder, null=False, blank=False, related_name="actions")

    STATUS_CHOICES = (
        (100, 'Scheduled 1st Request'),
        (200, 'Sent 1st Request'),
        (300, 'Scheduled 2nd Request'),
        (400, 'Sent 2nd Request'),
        (500, 'Awaiting Response'),
        (600, 'Incomplete'),
        (700, 'Complete'),
    )

    status = models.IntegerField(choices = STATUS_CHOICES, blank=False, null=False)
    scheduled_time = models.DateTimeField(blank=False, null=False)
    event_time = models.DateTimeField(blank=False, null=False)

    request_count = models.IntegerField(default=0, blank=False, null=False)


    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)

    def minutes_until(self):

        minutes, seconds = divmod((self.event_time - timezone.now()).total_seconds(), 60)

        if minutes <=0 :
            return None

        return int(minutes) + 1


    def process(self):

        if self.status == 100:

            minutes_until = self.minutes_until()

            if self.reminder.kind == 100:
                msg = "Hello %s, PARENT_NAME wants you to be ready for %s in %s minutes (%s). Are you ready?" % (
                    self.reminder.child.first_name,
                    self.reminder.for_desc,
                    self.minutes_until(),
                    self.reminder.child.user.local_time(self.event_time).strftime('%I:%M %p')
                )
            else:
                raise Exception("kind_not_handled")

            client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)
            sms = client.messages.create(to=self.reminder.child.phone_number, from_=settings.TWILIO_FROM_NUMBER, body=msg)


    @staticmethod
    def process_by_id(action_id):

        action = Action.objects.get(id=action_id)
        action.process()


    def handle_response(self):

        pass

    @staticmethod
    def gen_slug(user_id, reminder_id, schedule_time):

        slug = "s_%s_%s_%s" % (
            user_id,
            reminder_id,
            schedule_time.strftime("%Y-%m-%dT%H:%M")
        )

        return slug

    @staticmethod
    def schedule_for_user(user_id, reminder_id, schedule_time, event_time, skip_check=False):

        slug = Action.gen_slug(user_id, reminder_id, event_time)

        try:
            action = Action.objects.get(slug=slug)
        except ObjectDoesNotExist:
            action = Action()

        action.slug = slug
        action.reminder_id = reminder_id
        action.status = 100
        action.scheduled_time = schedule_time
        action.event_time = event_time

        action.save()