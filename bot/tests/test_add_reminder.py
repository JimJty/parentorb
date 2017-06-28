import json

from django.test import TestCase
from mock import mock

from bot.logic import route_logic


class Test(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _load_event(self, event_name):

        event = open("bot/test_events/%s.json" % event_name,"rb")
        event = json.loads(event.read())
        return event

    @mock.patch('core.fb_api_wrapper.Messenger.get_profile', return_value=None)
    def test_intro(self, get_profile):

        event = self._load_event("AddReminder")

        route_logic(event)

