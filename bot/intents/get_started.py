from base import Intent as BaseIntent


class Intent(BaseIntent):

    def do_logic(self):

        #three cases
        # no children
        # no reminders
        # reminders

        child_count = self.user.get_children().count()
        reminder_count = self.user.get_reminders().count()

        if child_count == 0:

            return self._resp_intro()

        elif reminder_count == 0:

            return self._resp_reminders()

        else:

            return self._resp_aready_started()

    def _resp_intro(self):

        self.reset_session()

        resp = {
            "dialogAction": {
                "type": "ElicitIntent",
                "message": {
                    "contentType": "PlainText",
                    "content": "Welcome, I am ParentOrb and I can automate repetitive reminders with your child, like being ready at a certain time, chores, and curfews."
                },
                "responseCard": {
                    "version": 1,
                    "contentType": "application/vnd.amazonaws.card.generic",
                    "genericAttachments": [
                        {
                            "title": "Let's add your first child.",
                            "buttons": [
                                {
                                    "text": "Add Child",
                                    "value": "Add Child"
                                }
                            ]
                        }
                    ]
                }
            },
            "sessionAttributes": self.session,
        }

        return resp

    def _resp_reminders(self):

        self.reset_session()

        resp = {
            "dialogAction": {
                "type": "ElicitIntent",
                "message": {
                    "contentType": "PlainText",
                    "content": "Let's continue, add a reminder:"
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

    def _resp_aready_started(self):

        self.reset_session()

        resp = {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": "You're back! Try 'Update Me'."
                },
            },
            "sessionAttributes": self.session,
        }

        return resp


