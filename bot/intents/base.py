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

    def build_template(self, case, resp_type, text=None, menu_title=None, menu_buttons=None):

        self.session["last_case"] = case

        resp = {
            "dialogAction": {
                "type": resp_type,
            },
            "sessionAttributes": self.session,
        }

        if text:
            resp['message'] = {
                "contentType": "PlainText",
                "content": text
            }

        if menu_title and menu_buttons:
             resp['responseCard'] = {
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