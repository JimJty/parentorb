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
            if upcoming:
                msg = "Upcoming:\n %s" % "\n".join(upcoming)
            else:
                msg = "You're good, no upcoming events."

            return self.build_template(
                case="no_action_default",
                resp_type=self.RESP_CLOSE,
                text=msg,
            )



