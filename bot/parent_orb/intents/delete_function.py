from bot.base_intent import Intent as BaseIntent, MenuButton

class Intent(BaseIntent):

    def do_logic(self):

        #cases
        # delete_account
        # delete_child
        # delete_reminder
        # default

        obj_selected = self.slot_value('object').lower() if self.slot_value('object') else None

        # delete_account
        if obj_selected == 'account':

            if self.confirmation is None:

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CONFIRM,
                    text="Whoa, DELETE your account?",
                    menu_title="Confirm:",
                    menu_buttons=[
                        MenuButton("Yes", "yes"),
                        MenuButton("No", "no"),
                    ]
                )
            elif self.confirmation is True:

                self.user.delete()

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CLOSE,
                    text="Poof, account deleted.",
                )
            else:

                return self.build_template(
                    case="delete_account",
                    resp_type=self.RESP_CLOSE,
                    text="Your account was not deleted.",
                )


        # delete_child
        if obj_selected == 'child':

            if not self.slot_value('object_id'):

                children = self.user.get_children()
                if children.count() == 0:
                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_CLOSE,
                        text="You have no children setup in your account.",
                    )
                else:

                    msg = "Which number:"
                    counter = 1
                    child_list = "|".join([str(c.id) for c in children])
                    self.set_session_value('child_list', child_list)

                    for c in children:
                        msg+= "\n %s) %s" % (counter, c.first_name)
                        counter += 1

                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_SLOT,
                        slot="object_id",
                        text=msg,
                    )

            else:

                child_id = self.extract_object_id("child_list")
                selected_child = self.user.get_child_by_id(child_id)
                if not selected_child:
                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_CLOSE,
                        text="Child not found.",
                    )


                if self.confirmation is None:

                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_CONFIRM,
                        text="Are you sure you want to delete %s's account?" % selected_child.first_name,
                        menu_title="Confirm:",
                        menu_buttons=[
                            MenuButton("Yes", "yes"),
                            MenuButton("No", "no"),
                        ]
                    )
                elif self.confirmation is True:

                    selected_child.delete()

                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_CLOSE,
                        text="Poof, child account deleted.",
                    )
                else:

                    return self.build_template(
                        case="delete_child",
                        resp_type=self.RESP_CLOSE,
                        text="Nothing was deleted.",
                    )





        # default
        return self.build_template(
            case="default",
                resp_type=self.RESP_CLOSE,
                text="What do you want to delete?",
                menu_title="You can:",
                menu_buttons=[
                    MenuButton("Delete Reminder", "delete reminder"),
                    MenuButton("Delete Child", "delete child"),
                    MenuButton("Delete Account", "delete account"),
                ]
        )


