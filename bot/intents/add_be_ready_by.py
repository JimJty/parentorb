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
                case="missing_child",
                resp_type=self.RESP_CLOSE,
                text="You haven't added any children yet.",
                menu_title="You can:",
                menu_buttons=[
                    MenuButton("Add Child", "Add Child"),
                ]
            )

        #missing_timezone
        # if self.user.time_offset is None:
        #     return self.build_template(
        #         case="missing_timezone",
        #         resp_type=self.RESP_CLOSE,
        #         text="You need to setup your account up first.",
        #         menu_title="You can:",
        #         menu_buttons=[
        #             MenuButton("Setup Account", "Setup Account"),
        #         ]
        #     )

        #can child be derived
        # if not self.slot_value('child') and child_count == 1:
        #     children = self.user.get_children()
        #     self.set_slot_value('child',children[0].first_name)
        #     self.set_session_value('child_id',children[0].id)

        #no_slot_child
        if not self.slot_value('child'):

            children = self.user.get_children()
            buttons = []
            for c in children:
                buttons.append(MenuButton(c.first_name,c.first_name))

            return self.build_template(
                case="no_slot_child",
                resp_type=self.RESP_SLOT,
                slot="child",
                text="For who?",
                menu_title="Select:",
                menu_buttons=buttons,
            )

        # #get the child id
        # if not self.session_value('child_id'):
        #
        #
        #     child = self.user.get_child_by_name(self.slot_value('child'))
        #     self.set_session_value('child_id', child.id)
        #
        # #no_slot_time
        # if not self.slot_value('time'):
        #
        #     return self.build_template(
        #         case="no_slot_time",
        #         resp_type=self.RESP_SLOT,
        #         slot="child",
        #         text="What time?",
        #     )






