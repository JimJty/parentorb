from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # list_children
        # list reminders
        # default

        obj_selected = self.slot_value('object').lower() if self.slot_value('object') else None



        # default
        return self.build_template(
            case="default",
                resp_type=self.RESP_CLOSE,
                text="What do you want list?",
                menu_title="You can:",
                menu_buttons=[
                    MenuButton("List Reminders", "list reminders"),
                    MenuButton("List Children", "list children"),
                ]
        )


