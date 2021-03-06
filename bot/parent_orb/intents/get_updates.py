from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # updates

        #updates

        upcoming = self.user.get_upcoming()
        past = self.user.get_recent_past()
        msg = ""

        if upcoming:
            msg = "Upcoming:"
            for u in upcoming[:3]:
                msg += "\n * %s" % u
        else:
            msg += "Upcoming:\n\n * Nothing Yet"

        if past:
            msg += "\n\nRecent:"
            for p in past[:3]:
                msg += "\n * %s" % p

        return self.build_template(
            case="updates",
            resp_type=self.RESP_CLOSE,
            text=msg,
        )






