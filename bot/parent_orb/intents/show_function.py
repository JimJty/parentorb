from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # list_children
        # list reminders
        # default

        obj_selected = self.slot_value('object').lower() if self.slot_value('object') else None

        #list_reminders
        if obj_selected in ("reminders",):

            reminders = self.user.get_reminders(True)

            msg = "Reminders:"
            counter = 1

            for r in reminders:
                msg+= "\n\n#%s. %s" % (counter, r.display())
                counter += 1

            return self.build_template(
                case="list_reminders",
                resp_type=self.RESP_CLOSE,
                text=msg,
                fulfilled=True,
            )

        #list_children
        if obj_selected in ("children",):

            children = self.user.get_children()

            msg = "Children:"
            counter = 1

            for c in children:
                msg+= "\n\n#%s. %s" % (counter, c.first_name)
                counter += 1

            return self.build_template(
                case="list_children",
                resp_type=self.RESP_CLOSE,
                text=msg,
                fulfilled=True,
            )


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


