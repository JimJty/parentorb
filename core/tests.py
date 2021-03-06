# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta, datetime

from django.test import TestCase
from django.utils import timezone
from mock import mock, patch

from core.fb_api_wrapper import FacebookException
from core.models import AppUser, Child, Action, Reminder


class TestAppUser(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        AppUser.objects.all().delete()
        Child.objects.all().delete()


    @mock.patch('core.fb_api_wrapper.Messenger.get_profile')
    def test_setup(self, get_profile):

        facebook_data = {
            "profile_pic": "https://scontent.xx.fbcdn.net/v/t1.0-1/387900_111423898972930_532477064_n.jpg?oh=b0a2ee0279851025f4cdecfbbbf7d30c&oe=59DDB290",
            "first_name": "Johnny",
            "last_name": "Tester",
            "locale": "en_US",
            "gender": "male",
            "timezone": -7,
            "is_payment_enabled": True
        }

        get_profile.return_value= facebook_data

        user = AppUser.setup("testid")

        self.assertEquals(facebook_data['first_name'], user.first_name)
        self.assertEquals(facebook_data['last_name'], user.last_name)
        self.assertNotEquals(user.custom_data, {})

        user2 = AppUser.setup("testid")

        self.assertEquals(user2.id, user.id)

        user.add_child("Jane", "+16027226814")

        self.assertEquals(user.children.all().count(), 1)

    @mock.patch('core.fb_api_wrapper.Messenger.get_profile', side_effect=FacebookException)
    def test_setup_no_facebook(self, get_profile):

        user = AppUser.setup("testid")

        self.assertNotEquals(user.id, None)
        self.assertEquals(user.first_name, None)

        user2 = AppUser.setup("testid")

        self.assertEquals(user2.id, user.id)

    @mock.patch('core.fb_api_wrapper.Messenger.get_profile')
    def test_timezone(self, get_profile):

        facebook_data = {
            "profile_pic": "https://scontent.xx.fbcdn.net/v/t1.0-1/387900_111423898972930_532477064_n.jpg?oh=b0a2ee0279851025f4cdecfbbbf7d30c&oe=59DDB290",
            "first_name": "Johnny",
            "last_name": "Tester",
            "locale": "en_US",
            "gender": "male",
            "timezone": -7,
            "is_payment_enabled": True
        }

        get_profile.return_value= facebook_data

        user = AppUser.setup("testid")

        self.assertNotEquals(user.local_time(),None)

        print user.relevant_server_time("17:30")


class TestActions(TestCase):

    def setUp(self):

        facebook_data = {
            "profile_pic": "mypic.jpg",
            "first_name": "Johnny",
            "last_name": "Tester",
            "locale": "en_US",
            "gender": "male",
            "timezone": -7,
            "is_payment_enabled": True
        }

        self.patcher = patch('core.fb_api_wrapper.Messenger.get_profile', return_value=facebook_data)
        self.patcher.start()

        self.patcher2 = patch('twilio.rest.Client.messages')
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

        AppUser.objects.all().delete()

    def test_add_action(self):

        user = AppUser.setup("test_id")

        child = user.add_child("Jill", "555")

        user.add_reminder(
            child_id = child.id,
            kind = 100,
            for_desc = 'brand practice',
            is_repeated = False,
            choosen_date = "2017-08-01",
            reminder_time = "16:30",
            days_selected = None
        )

        user.add_reminder(
            child_id = child.id,
            kind = 100,
            for_desc = 'brand practice',
            is_repeated = True,
            choosen_date = None,
            reminder_time = "16:30",
            days_selected = '0|1|2|5'
        )

        user.schedule_actions()

        self.assertEquals(Action.objects.all().count(),5)

        user.schedule_actions()

        self.assertEquals(Action.objects.all().count(),5)


    def test_process(self):

        user = AppUser.setup("test_id")

        child = user.add_child("Jill", "555")

        user.add_reminder(
            child_id = child.id,
            kind = 100,
            for_desc = 'brand practice',
            is_repeated = False,
            choosen_date = "2017-08-01",
            reminder_time = "16:30",
            days_selected = None
        )

        user.schedule_actions()

        action = Action.objects.all()[0]

        action.process()