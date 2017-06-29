import re

from core.models import AppUser


class Intent:

    RESP_SLOT = "ElicitSlot"
    RESP_INTENT = "ElicitIntent"
    RESP_CLOSE = "Close"

    def __init__(self):

        self.intent = None
        self.session = {}
        self.source = None
        self.slots = {}
        self.confirmation = None
        self.input = None
        self.user_id = None
        self.user = None
        self.attempt_count = 0
        self.last_case = None
        self.current_slot = None

    def setup(self, event):

        self.intent = event.get("currentIntent").get("name")
        self.session = event.get("sessionAttributes",{}) or {}
        self.source = event.get("invocationSource")
        self.slots = event.get("currentIntent").get("slots", {})
        self.confirmation = event.get("currentIntent").get("confirmationStatus")
        self.input = event.get("inputTranscript", None)
        self.user_id = event.get("userId", None)
        self.last_case = self.session_value('last_case')
        self.current_slot = self.session_value('current_slot')

        self.user = None
        if self.user_id:
            self.user = AppUser.setup(self.user_id)

        if self.current_slot:
            self.increment_attempt(self.current_slot)


    def reset_session(self):
        self.session = {}

    def slot_value(self,key_name):

        return self.slots.get(key_name, None)

    def set_slot_value(self,key_name, value):

        self.slots[key_name] = value

    def session_value(self, key_name):

        return self.session.get(key_name, None)

    def set_session_value(self,key_name, value):

        self.session[key_name] = value

    def extract_record_id(self):

        if self.input and self.input.startswith("record_id|"):
            return self.input.split("record_id|")[1]

        return None

    def inject_record_id(self, value):

        return "record_id|%s" % value

    def increment_attempt(self, slot):
        key_name="slot_attempt_%s" % slot
        current_count = int(self.session_value(key_name) or '0')
        current_count += 1
        self.set_session_value(key_name,current_count)

    def slot_attempt(self, slot):
        key_name="slot_attempt_%s" % slot
        return int(self.session_value(key_name) or '0')

    def build_template(self, case, resp_type, slot=None, text=None, menu_title=None, menu_buttons=None, fulfilled=False):

        if self.current_slot:
            self.increment_attempt(slot)

        self.session["last_case"] = case

        resp = {
            "dialogAction": {
                "type": resp_type,
            },
            "sessionAttributes": self.session,
        }

        if resp_type == self.RESP_CLOSE:
            if fulfilled:
                resp["dialogAction"]["fulfillmentState"] = "Fulfilled"
            else:
                resp["dialogAction"]["fulfillmentState"] = "Failed"

        if resp_type == self.RESP_SLOT:
            resp["dialogAction"]["slotToElicit"] = slot
            resp["dialogAction"]["intentName"] = self.intent
            resp["dialogAction"]["slots"] = self.slots
            self.set_session_value("current_slot",slot)
        else:
            self.set_session_value("current_slot",None)

        if text:
            resp["dialogAction"]['message'] = {
                "contentType": "PlainText",
                "content": text
            }

        if menu_title and menu_buttons:
             resp["dialogAction"]['responseCard'] = {
                "version": 1,
                "contentType": "application/vnd.amazonaws.card.generic",
                "genericAttachments": [
                    {
                        "title": menu_title,
                        "buttons": self._build_menu_buttons(menu_buttons),
                    }
                ]
            }

        return resp

    @staticmethod
    def _build_menu_buttons(buttons):
        template = []
        for b in buttons:
            template.append(
                {
                    "text": b.text,
                    "value": b.value,
                }
            )
        return template

    @staticmethod
    def resp_generic(event):

        resp = {
            "dialogAction": {
                "type": "ElicitIntent",
                "message": {
                    "contentType": "PlainText",
                    "content": "I'm not sure what to do."
                },
                "responseCard": {
                    "version": 1,
                    "contentType": "application/vnd.amazonaws.card.generic",
                    "genericAttachments": [
                        {
                            "title": "Try:",
                            "buttons": [
                                {
                                    "text": "Update Me",
                                    "value": "update me"
                                },
                            ]
                        }
                    ]
                }
            },
            "sessionAttributes": {},
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
            return Intent.resp_generic(event)


class MenuButton(object):

    def __init__(self, text, value):

        self.text = text
        self.value = value