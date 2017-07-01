import json

from django.test import TestCase
from mock import patch

from bot.logic import route_logic

import logging

from core.models import AppUser

logging.basicConfig()

class Test(TestCase):

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

        self.slots = {
            "phone_number": None,
            "code": None,
            "child": None,
            "schedule_type": None,
        }

    def tearDown(self):
        self.patcher.stop()

        AppUser.objects.all().delete()


    def _build_test_event(self, intent, slots, transcript=None, session=None, invocation=None, confirmation=None):

        if not invocation:
            invocation = "DialogCodeHook"

        if not confirmation:
            confirmation = "None"

        if not transcript:
            transcript = "-"

        event = dict(
            userId = "testid",
            inputTranscript = transcript,
            invocationSource = invocation,
            outputDialogMode = "Text",
            messageVersion = "1.0",
            sessionAttributes = session
        )

        event["currentIntent"] =  {
            "slots": slots,
            "name": intent,
            "confirmationStatus": confirmation
        }

        event["bot"] = {
            "alias": None,
            "version": "$LATEST",
            "name": "ParentOrb"
        }

        return event


    def test_missing_child(self):

        event = self._build_test_event(
            "AddBeReadyBy",
            self.slots,
            "add be ready by"
        )

        resp = route_logic(event)

        self._test_intent_case(resp,"missing_child")

    def test_missing_timezone(self):

        user = AppUser.setup("testid")
        user.add_child("Jane","555")
        user.time_offset = None
        user.save()

        event = self._build_test_event(
            "AddBeReadyBy",
            self.slots,
            "add be ready by"
        )

        resp = route_logic(event)

        self._test_intent_case(resp,"missing_timezone")

    def test_no_slot_child_1(self):

        user = AppUser.setup("testid")
        user.add_child("Jane","555")

        event = self._build_test_event(
            intent="AddBeReadyBy",
            slots=self.slots,
        )

        resp = route_logic(event)

        #child can be derived so it will move on
        self._test_intent_case(resp,"no_slot_time")

    def test_no_slot_child_2(self):

        user = AppUser.setup("testid")
        user.add_child("Jane","555")
        user.add_child("Jill","444")

        event = self._build_test_event(
            intent="AddBeReadyBy",
            slots=self.slots,
        )

        resp = route_logic(event)

        #child can't be derived so ask
        self._test_intent_case(resp,"no_slot_child")

    def test_no_slot_child_3(self):

        user = AppUser.setup("testid")
        child = user.add_child("Jane","555")
        user.add_child("Jill","444")

        event = self._build_test_event(
            intent="AddBeReadyBy",
            slots=self.slots,
            transcript="record_id|-1",
        )

        resp = route_logic(event)

        #incorrect child id
        self._test_intent_case(resp,"no_slot_child")

        #correct child id
        event = self._build_test_event(
            intent="AddBeReadyBy",
            slots=self.slots,
            transcript="record_id|%s" % child.id,
            session = {
                "last_case": "no_slot_child",
                "current_slot": "child",
                "attempt_count": 1
            }
        )

        resp = route_logic(event)

        #correct, move on
        self._test_intent_case(resp,"no_slot_time")

    def test_no_slot_time(self):
        user = AppUser.setup("testid")
        child = user.add_child("Jane","555")

        self.slots['child'] = child.first_name
        self.slots['time'] = "zzzz"

        event = self._build_test_event(
            intent="AddBeReadyBy",
            slots=self.slots,
            session = {
                "last_case": "no_slot_time",
                "current_slot": "time",
                "attempt_count": 1
            }
        )

        resp = route_logic(event)

        #self._test_intent_case(resp,"no_slot_time")


    def _test_intent_case(self, resp, case_name):

        self.assertEquals(resp.get("sessionAttributes",{}).get('last_case',None), case_name)

