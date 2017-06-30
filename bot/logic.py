import hashlib
import importlib
import json
import random
import re
import traceback

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from bot.intents.base import Intent
from core.models import AppUser
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


MAX_CHILDREN = 3

def route_logic(event):
    logger.info("Event: %s", json.dumps(event, indent=4))

    try:
        intent = event.get("currentIntent", {}).get("name", None)

        intent_obj = init_intent(intent)

        if intent == "AddChild":
            result = handle_add_child(event)
        elif intent_obj:
            result = intent_obj.handle(event)
        else:
            result = Intent.resp_generic(event)

        logger.info("Result: %s", json.dumps(result, indent=4))
        return result

    except Exception:

        #log exception
        logger.error(traceback.format_exc())

        #mail exception
        subject = 'ParentOrb Bot Exception'
        msg = "An exception occurred: %s" % timezone.now()
        msg += "\n\n%s" % traceback.format_exc()

        msg += "\n\n%s" % json.dumps(event, indent=4)

        email = EmailMessage(subject, msg, settings.SERVER_EMAIL, (settings.SERVER_EMAIL,))
        email.send()

        raise







def get_unhandled_resp(event):

    return {"dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "ParentOrb couldn't handle your request. Please try starting again."
            },
        }}

def handle_add_child(event):

    source = event.get("invocationSource", None)
    slots = event.get("currentIntent", {}).get("slots", None)
    intent = event.get("currentIntent", {}).get("name", None)
    session = event.get("sessionAttributes",{}) or {}

    userId = event.get("userId")
    user = AppUser.setup(userId)

    if source == "DialogCodeHook":

        if not getSlotVar(slots, 'child'):

            session["phone_attempts"] = 0
            session["validated_phone"] = "0"
            session["has_validated_code"] = "0"
            session["validation_code"] = ""
            session["validation_attempts"] = 0

            current_child_count = user.children.all().count()
            if current_child_count >= MAX_CHILDREN:
                return { "dialogAction" :{
                        "type": "Close",
                        "fulfillmentState": "Failed",
                        "message": {
                            "contentType": "PlainText",
                            "content": "You can only add up to 5 children."
                        }
                    }, "sessionAttributes": session,}
            else:
                return {"dialogAction": {
                    "type": "Delegate",
                    "slots": slots,
                }, "sessionAttributes": session,}

        elif not getSlotVar(slots, 'phone_number'):

            session["phone_attempts"] = int(session.get('phone_attempts',0)) + 1

            if session["phone_attempts"] > 1 and session["phone_attempts"] < 4:
                return { "dialogAction" :{
                    "type": "ElicitSlot",
                    "message": {
                        "contentType": "PlainText",
                        "content": "The phone number appears to be invalid, try entering just numbers."
                    },
                    "intentName": intent,
                    "slots": slots,
                    "slotToElicit": "phone_number",
                }, "sessionAttributes": session,}
            if session["phone_attempts"] >= 4:
                return { "dialogAction" :{
                    "type": "Close",
                    "fulfillmentState": "Failed",
                    "message": {
                        "contentType": "PlainText",
                        "content": "Sorry, we didn't understand your phone number. Try starting over."
                    }
                }, "sessionAttributes": session,}
            else:


                return {"dialogAction": {
                    "type": "Delegate",
                    "slots": slots,
                }, "sessionAttributes": session,}

        elif not getSlotVar(slots, 'code'):

            validated_phone = session.get("validated_phone", "0") == "1"
            phone_number = getSlotVar(slots, 'phone_number')

            if not validated_phone  and phone_number:
                client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)

                try:
                    resp = client.lookups.phone_numbers(phone_number).fetch()

                    session["validated_phone"] = "1"
                    slots["phone_number"] = resp.phone_number

                    validation_code = ''.join(random.SystemRandom().choice(['1','2','3','4','5','6','7','8','9']) for _ in range(5))

                    hashed_code =  hashlib.md5()
                    hashed_code.update("%s%s" % (validation_code, settings.SECRET_KEY ))
                    session["validation_code"] = hashed_code.hexdigest()

                    msg_body = "Hello, your parent is using ParentOrb. Please send them this code: %s" % validation_code

                    try:
                        client.messages.create(to=phone_number, from_=settings.TWILIO_FROM_NUMBER, body=msg_body)
                    except Exception, inst:
                        raise Exception("sms_send_error:%s" % inst)

                    return {"dialogAction": {
                        "type": "Delegate",
                        "slots": slots,
                    }, "sessionAttributes": session, }


                except TwilioRestException:

                    session["phone_attempts"] = 0
                    slots["phone_number"] = None

                    return {"dialogAction": {
                        "type": "ElicitSlot",
                        "message": {
                            "contentType": "PlainText",
                            "content": "The phone number was not valid, make sure to include the area code."
                        },
                        "intentName": intent,
                        "slots": slots,
                        "slotToElicit": "phone_number",
                    }, "sessionAttributes": session, }

            return {"dialogAction": {
                        "type": "Delegate",
                        "slots": slots,
                    }, "sessionAttributes": session, }

        elif getSlotVar(slots, 'code'):

            has_validated_code= session.get("has_validated_code", "0") == "1"
            session["validation_attempts"] = int(session.get('validation_attempts',0)) + 1
            code = getSlotVar(slots, 'code')

            if not has_validated_code:
                validation_code = session["validation_code"]
                hashed_code =  hashlib.md5()
                hashed_code.update("%s%s" % (code, settings.SECRET_KEY ))
                if validation_code == hashed_code.hexdigest():

                    #add the child to the user
                    user.add_child(getSlotVar(slots, 'child'), getSlotVar(slots, 'phone_number'))

                    return {"dialogAction":
                        {
                            "type": "ElicitIntent",
                            "message": {
                                "contentType": "PlainText",
                                "content": "Great, %s has been added!" % getSlotVar(slots, 'child')
                            },
                            "responseCard": {
                                "version": 1,
                                "contentType": "application/vnd.amazonaws.card.generic",
                                "genericAttachments": [
                                    {
                                        "title": "Now, add your first reminder.",
                                        "buttons": [
                                            {
                                                "text": "Add Reminder",
                                                "value": "Add Reminder"
                                            }
                                        ]
                                    }
                                ]
                            }
                        }, "sessionAttributes": {}, }
                elif session["validation_attempts"] > 2:
                    return { "dialogAction" :{
                        "type": "Close",
                        "fulfillmentState": "Failed",
                        "message": {
                            "contentType": "PlainText",
                            "content": "Sorry, we couldn't verify your number. Try starting over."
                        }
                    }, "sessionAttributes": session,}
                else:
                    slots["code"] = None

                    return {"dialogAction": {
                        "type": "ElicitSlot",
                        "intentName": intent,
                        "message": {
                            "contentType": "PlainText",
                            "content": "That code was incorrect, try again."
                        },
                        "slots": slots,
                        "slotToElicit": "code",
                    }, "sessionAttributes": session, }


            return {"dialogAction": {
                        "type": "Delegate",
                        "slots": slots,
                    }, "sessionAttributes": session, }




        else:
            return {"dialogAction": {
                "type": "Delegate",
                "slots": slots,
            }, "sessionAttributes": session, }



    return get_unhandled_resp(event)


#helpers

def init_intent(intent_name):

    if not intent_name:
        return None

    intent_name = convert_camelcase(intent_name)

    try:
        module = importlib.import_module("bot.intents.%s" % intent_name)
        cls = getattr(module, 'Intent')

        obj = cls()

        return obj

    except ImportError:
        return None

def convert_camelcase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def getSesVar(event, key_name):

    return event.get('sessionAttributes',{}).get(key_name, None)

def getSlotVar(slots, key_name):

    return slots.get(key_name, None)