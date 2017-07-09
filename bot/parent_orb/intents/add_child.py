import datetime
import hashlib
import random
import time

from django.conf import settings
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from bot.base_intent import Intent as BaseIntent, MenuButton


class Intent(BaseIntent):

    MAX_CHILDREN = 3

    def do_logic(self):


        #no_child
        if not self.slot_value('child'):

            self.set_session_value("phone_attempts", 0)
            self.set_session_value("validated_phone", 0)
            self.set_session_value("has_validated_code", 0)
            self.set_session_value("validation_code", 0)
            self.set_session_value("validation_attempts", 0)

            current_child_count = self.user.children.all().count()
            if current_child_count >= self.MAX_CHILDREN:
                return self.build_template(
                    case="no_child",
                    resp_type=self.RESP_CLOSE,
                    text="You can only add up to 5 children.",
                )
            else:
                return self.build_template(
                    case="no_child",
                    resp_type=self.RESP_DELEGATE,
                )

        #no_phone_number
        elif not self.slot_value('phone_number'):

            self.set_session_value("phone_attempts",int(self.session_value('phone_attempts') or 0) + 1)

            if self.session_value("phone_attempts") > 1 and self.session_value("phone_attempts") < 4:
                return self.build_template(
                    case="no_phone_number",
                    resp_type=self.RESP_SLOT,
                    slot="phone_number",
                    text="The phone number appears to be invalid, try entering just numbers.",
                )

            if self.session_value("phone_attempts") >= 4:
                return self.build_template(
                    case="no_phone_number",
                    resp_type=self.RESP_CLOSE,
                    text="Sorry, we didn't understand your phone number. Try starting over.",
                )
            else:
                return self.build_template(
                    case="no_child",
                    resp_type=self.RESP_DELEGATE,
                )

        #no_code
        elif not self.slot_value('code'):

            validated_phone = self.session_value("validated_phone") == "1"
            phone_number = self.slot_value('phone_number')

            if not validated_phone  and phone_number:
                client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)

                try:
                    resp = client.lookups.phone_numbers(phone_number).fetch()

                    self.set_session_value("validated_phone","1")
                    self.set_slot_value("phone_number", resp.phone_number)

                    validation_code = ''.join(random.SystemRandom().choice(['1','2','3','4','5','6','7','8','9']) for _ in range(5))

                    hashed_code =  hashlib.md5()
                    hashed_code.update("%s%s" % (validation_code, settings.SECRET_KEY ))
                    self.set_session_value("validation_code", hashed_code.hexdigest())

                    msg_body = "Hello, your parent is using ParentOrb. Please send them this code: %s" % validation_code

                    try:
                        client.messages.create(to=phone_number, from_=settings.TWILIO_FROM_NUMBER, body=msg_body)
                    except Exception, inst:
                        raise Exception("sms_send_error:%s" % inst)

                    return self.build_template(
                        case="no_code",
                        resp_type=self.RESP_DELEGATE,
                    )


                except TwilioRestException:

                    self.set_session_value("phone_attempts", 0)
                    self.set_slot_value("phone_number",None)

                    return self.build_template(
                        case="no_code",
                        resp_type=self.RESP_SLOT,
                        slot="phone_number",
                        text="The phone number was not valid, make sure to include the area code.",
                    )


            return self.build_template(
                case="no_code",
                resp_type=self.RESP_DELEGATE,
            )

        #has_code
        elif self.slot_value('code'):

            has_validated_code = self.session_value("has_validated_code") == "1"
            self.set_session_value("validation_attempts", int(self.session_value('validation_attempts') or 0) + 1)
            code = self.slot_value('code')

            if not has_validated_code:
                validation_code = self.session_value("validation_code")
                hashed_code =  hashlib.md5()
                hashed_code.update("%s%s" % (code, settings.SECRET_KEY ))

                if validation_code == hashed_code.hexdigest():

                    #add the child to the user
                    self.user.add_child(self.slot_value('child'), self.slot_value('phone_number'))

                    return self.build_template(
                        case="has_code",
                        resp_type=self.RESP_INTENT,
                        text="Great, %s has been added!" % self.slot_value('child'),
                        menu_title="Now, add a reminder:",
                        menu_buttons=[
                            MenuButton("Add Reminder", "Add Reminder"),
                        ]
                    )

                elif self.session_value("validation_attempts") > 2:

                    return self.build_template(
                        case="has_code",
                        resp_type=self.RESP_CLOSE,
                        text="Sorry, we couldn't verify your number. Try starting over.",
                    )

                else:
                    self.set_slot_value("code",None)

                    return self.build_template(
                        case="has_code",
                        resp_type=self.RESP_SLOT,
                        slot="code",
                        text="That code was incorrect, try again.",
                    )


            return self.build_template(
                case="no_code",
                resp_type=self.RESP_DELEGATE,
            )


        else:
            return self.build_template(
                case="no_code",
                resp_type=self.RESP_DELEGATE,
            )