from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # delete_account
        # delete_child
        # delete_reminder
        # default

        # delete_account
        if self.slot_value('object') == 'account':

            if self.confirmation is None:

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CONFIRM,
                    text="Whoa, DELETE your account?",
                )
            elif self.confirmation is True:

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CLOSE,
                    text="Poof, account deleted.",
                )
            else:

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CLOSE,
                    text="Your account was not deleted.",
                )


        # default
        return self.build_template(
            case="default",
                resp_type=self.RESP_CLOSE,
                text="What do you want to delete?",
                menu_title="You can:",
                menu_buttons=[
                    MenuButton("Delete Reminder", "delete reminder"),
                    MenuButton("Delete Child", "delete child"),
                    MenuButton("Delete Account", "delete account"),
                ]
        )


