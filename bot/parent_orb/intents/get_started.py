from bot.base_intent import Intent as BaseIntent, MenuButton


class Intent(BaseIntent):

    def do_logic(self):

        #three cases
        # no children
        # no reminders
        # reminders

        child_count = self.user.get_children().count()
        reminder_count = self.user.get_reminders().count()

        if not self.user.is_configured():
            self.reset_session()

            return self.build_template(
                case="not_configured",
                resp_type=self.RESP_INTENT,
                text="Welcome, I am ParentOrb and I can automate repetitive reminders with your child, like being ready at a certain time, chores, and curfews.",
                menu_title="Let's get you setup.",
                menu_buttons=[
                    MenuButton("Setup", "setup account"),
                ]
            )

        elif child_count == 0:

            self.reset_session()

            return self.build_template(
                case="no_child",
                resp_type=self.RESP_INTENT,
                text="Let's continue:",
                menu_title="Add your first child.",
                menu_buttons=[
                    MenuButton("Add Child", "add child"),
                ]
            )

        elif reminder_count == 0:

            self.reset_session()

            return self.build_template(
                case="no_reminder",
                resp_type=self.RESP_INTENT,
                text="Let's continue, add a reminder:",
                menu_title="Types",
                menu_buttons=[
                    MenuButton("Be Ready By", "add be ready by"),
                ]
            )

        else:

            self.reset_session()

            return self.build_template(
                case="default",
                resp_type=self.RESP_CLOSE,
                text="You're back! Try 'Update Me'.",

            )



