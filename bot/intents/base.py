import re

from core.models import AppUser


class Intent:

    def __init__(self):

        self.intent = None
        self.session = {}
        self.source = None
        self.slots = {}
        self.confirmation = None
        self.input = None
        self.user_id = None
        self.user = None

    def setup(self, event):

        self.intent = event.get("currentIntent").get("name")
        self.session = event.get("sessionAttributes",{}) or {}
        self.source = event.get("invocationSource")
        self.slots = event.get("currentIntent").get("slots", {})
        self.confirmation = event.get("currentIntent").get("confirmationStatus")
        self.input = event.get("inputTranscript", None)
        self.user_id = event.get("userId", None)

        self.user = None
        if self.user_id:
            self.user = AppUser.setup(self.user_id)

    def reset_session(self):
        self.session = {}

    def slot_value(self,key_name):

        return self.slots.get(key_name, None)

    def _resp_generic(self):

        resp = {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": "I'm not sure what to do. Please try starting again."
                },
            }
        }

        return resp

    def do_logic(self):
        raise Exception("logic_not_defined")

    def handle(self, event):

        self.setup(event)
        result = self.do_logic()

        if result:
            return result
        else:
            return self._resp_generic()

