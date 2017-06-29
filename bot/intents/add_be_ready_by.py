from base import Intent as BaseIntent, MenuButton
import time

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

        #some preinit
        if not self.slot_value('child'):
            self.reset_session()

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
        if self.user.time_offset is None:
            return self.build_template(
                case="missing_timezone",
                resp_type=self.RESP_CLOSE,
                text="You need to setup your account up first.",
                menu_title="You can:",
                menu_buttons=[
                    MenuButton("Setup Account", "Setup Account"),
                ]
            )

        #can child be derived
        if not self.session_value('child_id') and child_count == 1:
            children = self.user.get_children()
            self.set_slot_value('child',children[0].first_name)
            self.set_session_value('child_id',children[0].id)

        #was child entered
        if not self.session_value('child_id') and self.current_slot == 'child':
            child_id = self.extract_record_id()
            child = self.user.get_child_by_id(child_id)
            if child:
                self.set_slot_value('child',child.first_name)
                self.set_session_value('child_id',child.id)


        #no_slot_child
        if not self.slot_value('child'):

            children = self.user.get_children()
            buttons = []
            for c in children:
                buttons.append(MenuButton(c.first_name, self.inject_record_id(c.id)))

            return self.build_template(
                case="no_slot_child",
                resp_type=self.RESP_SLOT,
                slot="child",
                text="For who?",
                menu_title="Select:",
                menu_buttons=buttons,
            )


        #was time entered, was it good
        if self.slot_value('time'):
            try:
                time.strptime(self.slot_value('time'), '%H:%M')
            except ValueError:
                self.set_slot_value('time',None)


        #no_slot_time
        if not self.slot_value('time'):

            msg = "What time?"
            if self.attempt_count > 1:
                msg = "Hmm, what time?, enter something like 7:00am."

            return self.build_template(
                case="no_slot_time",
                resp_type=self.RESP_SLOT,
                slot="time",
                text=msg,
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






