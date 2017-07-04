from bot.base_intent import Intent as BaseIntent
from core.models import Child, AppUser


class Intent(BaseIntent):


    def __init__(self):
        BaseIntent.__init__(self)

        self.child = None
        self.action = None


    def get_user(self):

        self.child = Child.get_by_phone(self.user_id)
        if self.child:
            self.action = self.child.get_active_reminder()

        if self.child:
            return AppUser.setup(self.child.user.ref_id)
        else:
            return None

    def do_logic(self):

        #no_child
        if not self.child:
            return self.build_template(
                case="no_child",
                resp_type=self.RESP_CLOSE,
                text="It looks like your account has been removed, you'll need to talk with your parent to get setup again.",
            )

        #no_action_default
        if not self.action:

            upcoming = self.child.get_upcoming()
            past = self.child.get_recent_past()
            msg = ""
            if upcoming or past:
                if upcoming:
                    msg = "Upcoming:"
                    for u in upcoming[:3]:
                        msg += "\n * %s" % u
                else:
                    msg += "Upcoming:\n * Nothing Yet"

                if past:
                    msg += "\nRecent:"
                    for p in past[:3]:
                        msg += "\n * %s" % p


            else:
                msg = "You're good, no upcoming events."

            return self.build_template(
                case="no_action_default",
                resp_type=self.RESP_CLOSE,
                text=msg,
            )

        #action_default
        if self.action:

            resp = self.input.strip().lower()

            if resp == "yes" and not self.slot_value("more_info"):
                self.action.handle_child_resp(True)

                return self.build_template(
                    case="action_default",
                    resp_type=self.RESP_CLOSE,
                    text=self.action.reminder.resp_affirmative(),
                )

            elif resp == "no" and not self.slot_value("more_info"):

                is_final = self.action.minutes_until() <= 5
                if not is_final:
                    self.action.handle_child_resp(False, False)

                return self.build_template(
                    case="action_default",
                    resp_type=self.RESP_SLOT if is_final else self.RESP_CLOSE,
                    slot="more_info" if is_final else None,
                    text=self.action.reminder.resp_negative(is_final),
                )

            elif self.slot_value("more_info") and not self.action.excuse:

                excuse = self.input.strip()[:200]
                self.action.handle_child_resp(False, excuse)

                return self.build_template(
                    case="action_default",
                    resp_type=self.RESP_CLOSE,
                    text=self.action.reminder.resp_negative(True, True),
                )

            else:
                return self.build_template(
                    case="action_default",
                    resp_type=self.RESP_CLOSE,
                    text=self.action.reminder.resp_no_understand(),
                )


