import json

from mock import patch

from bot.base_intent import BaseIntentTest
from bot.logic import route_logic

import logging

from core.models import AppUser, Action

logging.basicConfig()

class Test(BaseIntentTest):

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

        }

    def tearDown(self):
        self.patcher.stop()

        AppUser.objects.all().delete()


    def test_no_child(self):

        user = AppUser.setup("testid")

        event = self.build_test_event(
            "ParentOrbChild",
            "CatchAll",
            self.slots,
            "hello"
        )

        resp = route_logic(event)

        self.check_intent_case(resp,"no_child")

    def test_no_action_default(self):

        user = AppUser.setup("testid")
        child = user.add_child("Jane","+555")

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

        event = self.build_test_event(
            "ParentOrbChild",
            "CatchAll",
            self.slots,
            "hello",
            userId="555"
        )

        resp = route_logic(event)

        #self._test_intent_case(resp,"missing_timezone")



    def _test_intent_case(self, resp, case_name):

        self.assertEquals(resp.get("sessionAttributes",{}).get('last_case',None), case_name)

