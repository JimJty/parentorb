from base import Intent as BaseIntent, MenuButton


class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # prereq (missing child, timezone)
        # no_slot_child
        # child_not_found
        # no_slot_time
        # invalid time
        # no event
        # confirmation
        # all good

        #missing_child
        child_count = self.user.get_children().count()
        if child_count == 0:

            return self.build_template(
                "missing_child",
                self.RESP_CLOSE,
                "You haven't added any children yet.",
                "You can:",
                [
                    MenuButton("Add Child", "Add Child"),
                ]
            )

        #missing_timezone
        if self.user.time_offset is None:
            return self.build_template(
                "missing_timezone",
                self.RESP_CLOSE,
                "You need to setup your account up first.",
                "You can:",
                [
                    MenuButton("Setup Account", "Setup Account"),
                ]
            )

        #no_slot_child
        if not self.slot_value('child'):

            children = self.user.get_children()

            return self.build_template(
                "no_slot_child",
                self.RESP_SLOT,
                "For who?",
                "You can:",
                [
                    MenuButton("Setup Account", "Setup Account"),
                ]
            )

        #child_not_found
        if not self.user.get_child_by_name(self.slot_value('child')):
            return

        #no_slot_time
        if not self.slot_value('time'):
            return






