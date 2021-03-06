# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime
import time

import pytz
from dateutil.tz import tzoffset, tzutc
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError, transaction
from django.db.models import Q
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
    nick_name = models.CharField(max_length=200, blank=True, null=True)
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

    def is_configured(self):

        if self.nick_name:
            return True
        else:
            return False

    def configure(self, nick_name):

        self.nick_name = nick_name
        self.save()

    def get_upcoming(self):

        upcoming = []

        future_date = timezone.now() + timedelta(days=8)

        reminders_present = []

        actions = Action.objects.filter(reminder__child__user=self, event_time__lte=future_date, status__in=(100,300,500)).order_by('event_time')
        for a in actions:
            if a.reminder_id not in reminders_present:
                upcoming.append(a.display())
                reminders_present.append(a.reminder_id)

        return upcoming

    def get_recent_past(self):

        past = []

        future_date = timezone.now() + timedelta(days=1)

        reminders_present = []

        actions = Action.objects.filter(reminder__child__user=self, event_time__lte=future_date, status__in=(600,700)).order_by('-event_time')
        for a in actions:
            if a.reminder_id not in reminders_present:
                past.append(a.display())
                reminders_present.append(a.reminder_id)

        return past

    def add_child(self, first_name, phone_number):

        if not first_name:
            first_name = "Child"

        child = Child.get_by_phone(phone_number)
        if child:
            child.first_name = first_name
            child.user = self
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

    def get_child_by_phone(self, phone_number):

        child = Child.get_by_phone(phone_number)
        if child and child.user == self:
            return child
        else:
            return None


    def get_children(self):

        children = self.children.all().order_by('first_name','id')

        return children

    def get_reminders(self, active_only=False):

        if not active_only:
            reminders = Reminder.objects.filter(child__user=self).order_by('id')
        else:
            reminders = Reminder.objects.filter(
                Q(child__user=self),
                Q(one_time__gte=timezone.now()) | Q(one_time__isnull=True)
            ).order_by('id')

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

    def get_reminder_by_id(self, reminder_id):

        reminder = Reminder.objects.filter(child__user=self, id=reminder_id)
        if reminder.count() == 1:
            return reminder[0]

        return None

    def add_reminder(self, child_id, kind, for_desc, is_repeated, choosen_date, reminder_time, days_selected):

        child = self.get_child_by_id(child_id)

        if not is_repeated:
            one_time =  self.relevant_server_time(reminder_time, choosen_date)
            days_selected = None
            reminder_time = None
        else:
            one_time = None
            days_selected = '|'.join(sorted(days_selected.split('|'))) #reorder

        reminder = Reminder()
        reminder.child = child
        reminder.kind = kind
        reminder.for_desc = for_desc
        reminder.one_time = one_time
        reminder.repeat_at_time = reminder_time
        reminder.repeat_days = days_selected
        reminder.active = True

        with transaction.atomic():

            reminder.save()
            self.schedule_actions()

            reminder.refresh_from_db()
            msg = "%s added a reminder for you: %s" % (
                self.nick_name,
                reminder.display_child(),
            )
            sms_client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)
            sms_client.messages.create(to=child.phone_number, from_=settings.TWILIO_FROM_NUMBER, body=msg)

        return reminder

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

    @staticmethod
    def get_users_to_schedule():

        sql = """
        SELECT
            distinct u.*
        FROM
            core_action a
            inner join core_reminder r on a.reminder_id = r.id
            inner join core_child c on r.child_id = c.id
            inner join core_appuser u on c.user_id = u.id
        WHERE
            r.repeat_at_time is not null
        """

        users = AppUser.objects.raw(sql)

        users_list = [u for u in users]
        return users_list


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

        actions = Action.objects.filter(reminder__child=self, status__in=(300,500)).order_by('event_time')

        if actions.count() > 0:
            return actions[0]
        else:
            return None

    def get_upcoming(self):

        upcoming = []

        future_date = timezone.now() + timedelta(days=8)

        reminders_present = []

        actions = Action.objects.filter(reminder__child=self, event_time__lte=future_date, status__in=(100,300,500)).order_by('event_time')
        for a in actions:
            if a.reminder_id not in reminders_present:
                upcoming.append(a.display_child())
                reminders_present.append(a.reminder_id)

        return upcoming

    def get_recent_past(self):

        past = []

        future_date = timezone.now() + timedelta(days=1)

        reminders_present = []

        actions = Action.objects.filter(reminder__child=self, event_time__lte=future_date, status__in=(600,700)).order_by('-event_time')
        for a in actions:
            if a.reminder_id not in reminders_present:
                past.append(a.display_child())
                reminders_present.append(a.reminder_id)

        return past


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

    def resp_no_understand(self):

        default = "I don't understand, are you ready for %s, yes or no?" % self.for_desc

        return default

    def resp_affirmative(self):

        default = "Great, I'll let %s know you are ready for %s." % (self.child.user.nick_name, self.for_desc,)

        return default

    def resp_negative(self, final=False, excuse=False):

        msg = "Ok, I'll check back later"

        if excuse:
            msg = "Ok, I'll let %s know." % self.child.user.nick_name
        elif final:
            msg = "What do you want me to tell %s?" % self.child.user.nick_name

        return msg

    def display(self):

        to_display = "%s for %s at %s" % (
            self.for_desc,
            self.child.first_name,
            self.display_time()
        )

        return to_display

    def display_child(self):

        to_display = "%s at %s" % (
            self.for_desc,
            self.display_time()
        )

        return to_display

    def display_time(self):

        if self.one_time:

            display_time = self.child.user.local_time(self.one_time)
            local_time_now = self.child.user.local_time()
            local_time_tomorrow = local_time_now + timedelta(days=1)

            if local_time_now.strftime("%Y-%m-%d") ==  display_time.strftime("%Y-%m-%d"):
                date_part = "Today"
            elif local_time_tomorrow.strftime("%Y-%m-%d") ==  display_time.strftime("%Y-%m-%d"):
                date_part = "Tomorrow"
            else:
                date_part = "on %s %s" % (display_time.strftime("%b"), get_ordinal(display_time.strftime("%d")))

            display_time = "%s %s" % (
                time_part(display_time),
                date_part
            )

        else:
            display_time = timezone.now().strftime("%Y-%m-%d") + "T" + self.repeat_at_time.strftime("%H:%M")
            display_time = datetime.strptime(display_time, "%Y-%m-%dT%H:%M")

            display_time = "%s on %s" % (
                time_part(display_time),
                ', '.join(self.display_repeat_times())
            )

        return display_time

    def display_repeat_times(self):

        selected_days = []
        for d in sorted(self.repeat_days.split('|')):
            if d == "0":
                selected_days.append("Mon")
            elif d == "1":
                selected_days.append("Tue")
            elif d == "2":
                selected_days.append("Wed")
            elif d == "3":
                selected_days.append("Thur")
            elif d == "4":
                selected_days.append("Fri")
            elif d == "5":
                selected_days.append("Sat")
            elif d == "6":
                selected_days.append("Sun")

        return selected_days

class Action(models.Model):

    slug = models.CharField(max_length=100, blank=False, null=False, unique=True)
    reminder = models.ForeignKey(Reminder, null=False, blank=False, related_name="actions")

    STATUS_CHOICES = (
        (100, 'Scheduled 1st Request'),
        #(200, 'Sent 1st Request'),
        (300, 'Scheduled 2nd Request'),
        #(400, 'Sent 2nd Request'),
        (500, 'Awaiting Response'),
        (600, 'Incomplete'),
        (700, 'Complete'),
    )

    status = models.IntegerField(choices = STATUS_CHOICES, blank=False, null=False)
    scheduled_time = models.DateTimeField(blank=False, null=False)
    event_time = models.DateTimeField(blank=False, null=False)

    request_count = models.IntegerField(default=0, blank=False, null=False)
    excuse = models.CharField(max_length=200, blank=True, null=True)
    was_parent_notified = models.BooleanField(default=False, null=False, blank=False)

    add_date = models.DateTimeField(blank=False, auto_now_add=True)
    edit_date = models.DateTimeField(blank=False, auto_now=True)

    LAST_CHANCE_MINUTES = 5

    def minutes_until(self):

        minutes, seconds = divmod((self.event_time - timezone.now()).total_seconds(), 60)

        if minutes <= 0 :
            return 0

        return int(minutes) + 1

    def display_child(self, include_name=False):


        local_time_now = self.reminder.child.user.local_time()
        local_time_tomorrow = local_time_now + timedelta(days=1)
        local_time_event = self.reminder.child.user.local_time(self.event_time)

        if local_time_now.strftime("%Y-%m-%d") ==  local_time_event.strftime("%Y-%m-%d"):
            date_part = "Today"
        elif local_time_tomorrow.strftime("%Y-%m-%d") ==  local_time_event.strftime("%Y-%m-%d"):
            date_part = "Tomorrow"
        else:
            date_part = "on %s %s" % (local_time_event.strftime("%b"), get_ordinal(local_time_event.strftime("%d")))

        if not include_name:
            msg = "%s at %s %s" % (
                self.reminder.for_desc,
                time_part(local_time_event),
                date_part,
            )
        else:
            msg = "%s: %s at %s %s" % (
                self.reminder.child.first_name,
                self.reminder.for_desc,
                time_part(local_time_event),
                date_part,
            )

        return msg

    def display(self):

        return self.display_child(True)

    def handle_child_resp(self, affirmative, final=False):

        if affirmative:
            self.status = 700
            self.save()
            self.notify_parent()
        else:
            if not final:
                self.status = 300
                before_event_time = self.event_time - timedelta(minutes=5)
                self.scheduled_time= before_event_time
                self.save()
            else:
                self.status = 600
                self.excuse = final
                self.save()
                self.notify_parent()

    def notify_parent(self):

        if not self.was_parent_notified:

            msg = None
            if self.status == 700:
                if self.reminder.kind == 100:
                    msg = "%s told me that they are ready for %s." % (
                        self.reminder.child.first_name,
                        self.reminder.for_desc,
                    )

            elif self.status == 600:

                if self.reminder.kind == 100:

                    if self.excuse == "no_response":
                        msg = "%s does not appear ready for %s. There was no response to my attempts to contact." % (
                            self.reminder.child.first_name,
                            self.reminder.for_desc,
                        )
                    elif self.excuse:
                        msg = "%s said they are NOT ready for %s. The reason: %s" % (
                            self.reminder.child.first_name,
                            self.reminder.for_desc,
                            self.excuse
                        )

            if msg:
                try:
                    m = Messenger(settings.FB_MESSENGER_TOKEN)
                    m.send_message(self.reminder.child.user.ref_id, msg)
                except FacebookException, inst:
                    logger.error("error sending fb msg: %s", inst)

                self.was_parent_notified = True
                self.save()




    def is_last_chance(self):

        return self.minutes_until() <= self.LAST_CHANCE_MINUTES

    def is_past_due(self):

        return self.minutes_until() <= 0

    def process(self):

        sms_client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)
        msg = None

        #handle no response
        if self.status == 500 and self.is_past_due():
            self.handle_child_resp(False, "no_response")
        elif self.status == 500 and self.request_count == 1 and self.is_last_chance():
            self.handle_child_resp(False, False)


        if self.reminder.kind == 100:

            if self.status == 100:
                msg = "Hello %s, %s wants you to be ready for %s in %s minutes (%s). Are you ready?" % (
                    self.reminder.child.first_name,
                    self.reminder.child.user.nick_name,
                    self.reminder.for_desc,
                    self.minutes_until(),
                    time_part(self.reminder.child.user.local_time(self.event_time))
                )

            elif self.status == 300:
                msg = "You need to be ready for %s in %s minutes! Are you ready?" % (
                    self.reminder.for_desc,
                    self.minutes_until(),
                )

        else:
            raise Exception("kind_not_handled")


        if msg:
            sms_client.messages.create(to=self.reminder.child.phone_number, from_=settings.TWILIO_FROM_NUMBER, body=msg)
            self.request_count += 1
            self.status = 500
            self.save()

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
            return action
        except ObjectDoesNotExist:
            action = Action()

        action.slug = slug
        action.reminder_id = reminder_id
        action.status = 100
        action.scheduled_time = schedule_time
        action.event_time = event_time

        action.save()

        return action

    @staticmethod
    def get_actions_to_process():

        actions = Action.objects.filter(status__in=(100,300,500), scheduled_time__lte=timezone.now()).order_by('id')

        return actions

#helper functions

def get_ordinal(day):

    day = int(day)

    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]

    return "%s%s" % (day,suffix)

def time_part(date_value):

    return "%s:%s%s" % (
        int(date_value.strftime("%I")),
        date_value.strftime("%M"),
        date_value.strftime("%p").lower(),
    )