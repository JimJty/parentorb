from bot.base_intent import Intent as BaseIntent


class Intent(BaseIntent):

    def do_logic(self):

        if not self.slot_value('kind'):

            return self._resp_intro()

    def _resp_intro(self):

        self.reset_session()

        resp = {
            "dialogAction": {
                "type": "ElicitIntent",
                "message": {
                  "contentType": "PlainText",
                  "content": "What type?"
                },
                "responseCard": {
                    "version": 1,
                    "contentType": "application/vnd.amazonaws.card.generic",
                    "genericAttachments": [
                        {
                            "title": "Types",
                            "buttons": [
                                {
                                    "text": "Be Ready By",
                                    "value": "add be ready by"
                                },
                                {
                                    "text": "Chore",
                                    "value": "add chore"
                                },
                                {
                                    "text": "Curfew",
                                    "value": "add curfew"
                                }
                            ]
                        }
                    ]
                }
            },
            "sessionAttributes": self.session,
        }

        return resp


