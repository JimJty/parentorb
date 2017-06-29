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
        }

    def tearDown(self):
        self.patcher.stop()

        AppUser.objects.all().delete()


    def _build_test_event(self, intent, slots, transcript, session=None, invocation=None, confirmation=None):

        if not invocation:
            invocation = "DialogCodeHook"

        if not confirmation:
            confirmation = "None"

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


        self._test_intent_case(event,"missing_child")

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

        self._test_intent_case(event,"missing_timezone")

    def _test_intent_case(self, event, case_name):

        resp = route_logic(event)

        self.assertEquals(resp.get("sessionAttributes",{}).get('last_case',None), case_name)

