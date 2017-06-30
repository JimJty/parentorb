import datetime

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
            self.increment_attempt('time')

            msg = "What time do you want %s to be ready?" % self.slot_value('child')

            if self.attempt_count('time') > 1:
                msg = "What time?, be more more specific, like 7:30am."

            return self.build_template(
                case="no_slot_time",
                resp_type=self.RESP_SLOT,
                slot="time",
                text=msg,
            )

        #no_event
        if not self.slot_value('event'):

            msg = "What does %s need to be ready for?" % self.slot_value('child')

            return self.build_template(
                case="no_event",
                resp_type=self.RESP_SLOT,
                slot="event",
                text=msg,
            )

        #no_schedule_type
        if not self.slot_value('schedule_type'):

            msg = "How often?"

            return self.build_template(
                case="no_schedule_type",
                resp_type=self.RESP_SLOT,
                slot="schedule_type",
                text=msg,
                menu_title="Select:",
                menu_buttons=[
                    MenuButton("Just Once", "once"),
                    MenuButton("Repeated", "repeated"),
                ]
            )

        #set is_repeated
        if self.session_value('is_repeated') is None:
            if self.slot_value('schedule_type').lower() in ('repeat','repeated'):
                self.set_session_value('is_repeated',"1")
            else:
                self.set_session_value('is_repeated',"0")
        is_repeated = self.session_value('is_repeated') == "1"


        #check if date is valid
        if not is_repeated and self.slot_value('date'):
            try:
                datetime.datetime.strptime(self.slot_value('date')[:10], "%Y-%m-%d")
            except ValueError:
                self.set_slot_value('date', None)


        #no_date
        if not is_repeated and not self.slot_value('date'):

            today = self.user.local_time().strftime("%Y-%m-%d")
            tomorrow = (self.user.local_time() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

            msg = "What day?"
            return self.build_template(
                case="no_date",
                resp_type=self.RESP_SLOT,
                slot="date",
                text=msg,
                menu_title="Select, or type a date:",
                menu_buttons=[
                    MenuButton("Today", today),
                    MenuButton("Tomorrow", tomorrow),
                ]
            )

        #no_repeat_day
        elif is_repeated and not self.session_value('repeat_days'):

            if self.current_slot == 'repeat_day':
                record_id = self.extract_record_id()
            else:
                record_id = None

            msg = None
            menu_title = None
            menu_buttons = None

            if not record_id and not self.slot_value('repeat_day'):
                msg = "What days?"
                menu_title="Select the days:"
                menu_buttons = [
                    MenuButton("Monday to Friday", "record_id|weekdays"),
                    MenuButton("Every Day", "record_id|everyday"),
                    MenuButton("Let Me Pick", "record_id|let_me_pick"),
                ]

            elif record_id == "weekdays":
                self.set_session_value('repeat_days',"0|1|2|3|4")

            elif record_id == "everyday":
                self.set_session_value('repeat_days',"0|1|2|3|4|5|6")

            elif record_id == "day_select_done" and not self.session_value('pending_repeat_days'):
                msg = "No days selected, type a day and submit."
                menu_title= "Days Selected: -"
                menu_buttons = [
                    MenuButton("I'm Done", "record_id|day_select_done"),
                ]

            elif record_id == "day_select_done" and self.session_value('pending_repeat_days'):
                self.set_session_value('repeat_days',self.session_value('pending_repeat_days'))

            else: #default loop

                msg, menu_title, menu_buttons = self._handle_day_selection()


            #do a final check to see if day selection is done
            if msg and not self.session_value('repeat_days'):

                return self.build_template(
                    case="no_repeat_day",
                    resp_type=self.RESP_SLOT,
                    slot="repeat_day",
                    text=msg,
                    menu_title=menu_title,
                    menu_buttons=menu_buttons
                )

        #complete
        if self.session_value('child_id') \
                and self.slot_value('event') \
                and self.slot_value('date') \
                and self.slot_value('time'):

            self.user.add_reminder(
                child_id = self.session_value('child_id'),
                kind = 100,
                for_desc = self.slot_value('event'),
                is_repeated = is_repeated,
                choosen_date = self.slot_value('date'),
                reminder_time = self.slot_value('time'),
                days_selected = self.session_value('repeat_days'),
            )

            self.reset_session()

            return self.build_template(
                case="complete",
                resp_type=self.RESP_CLOSE,
                fulfilled = True,
                text="Your reminder has been saved!",
            )

    def _handle_day_selection(self):

        pending_day_codes = []
        if self.session_value('pending_repeat_days'):
            pending_day_codes = self.session_value('pending_repeat_days').split("|")

        typed_day = self.slot_value('repeat_day')

        typed_day_code = None

        if typed_day:
            typed_day = typed_day.strip().lower()

            typed_day_code = None
            if typed_day in ('mon','monday'):
                typed_day_code = '0'
            elif typed_day in ('tue','tuesday'):
                typed_day_code = '1'
            elif typed_day in ('wed','wednesday'):
                typed_day_code = '2'
            elif typed_day in ('thur','thursday'):
                typed_day_code = '3'
            elif typed_day in ('fri','friday'):
                typed_day_code = '4'
            elif typed_day in ('sat','saturday'):
                typed_day_code = '5'
            elif typed_day in ('sun','sunday'):
                typed_day_code = '6'

            if typed_day_code is not None and typed_day_code not in pending_day_codes:

                pending_day_codes.append(typed_day_code)

        if pending_day_codes:
            self.set_session_value('pending_repeat_days','|'.join(pending_day_codes))
        else:
            self.set_session_value('pending_repeat_days', None)

        msg = "Type a day and submit."

        if not pending_day_codes:
            menu_title= "Days Submitted: -"
        else:
            selected_days = []
            for d in sorted(pending_day_codes):
                if d == "0":
                    selected_days.append("Mon")
                elif d == "1":
                    selected_days.append("Tue")
                elif d == "2":
                    selected_days.append("Wed")
                elif d == "3":
                    selected_days.append("Thur")
                elif d == "4":
                    selected_days.append("Fri")
                elif d == "5":
                    selected_days.append("Sat")
                elif d == "6":
                    selected_days.append("Sun")

            menu_title = "Days Submitted: " +  ", ".join(selected_days)

        menu_buttons = [
            MenuButton("I'm Done", "record_id|day_select_done"),
        ]

        return msg, menu_title, menu_buttons





