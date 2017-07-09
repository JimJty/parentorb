from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # no_nick_name
        # complete

        #no_nick_name
        if not self.slot_value('nick_name'):

            msg = "What do your kid(s) call you?"

            return self.build_template(
                case="no_nick_name",
                resp_type=self.RESP_SLOT,
                slot="nick_name",
                text=msg,
            )

        #complete
        elif self.slot_value('nick_name'):

            self.user.configure(self.slot_value('nick_name'))

            child_count = self.user.get_children().count()

            if child_count == 0:

                return self.build_template(
                    case="complete",
                    resp_type=self.RESP_INTENT,
                    text="Let's continue",
                    menu_title="Add your first child.",
                    menu_buttons=[
                        MenuButton("Add Child", "add child"),
                    ]
                )

            else:

                return self.build_template(
                    case="complete",
                    resp_type=self.RESP_CLOSE,
                    text="You are setup!",
                )




