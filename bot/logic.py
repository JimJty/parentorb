import hashlib
import json
import random

import requests
from django.conf import settings
from django.core.mail import EmailMessage
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from core.models import AppUser


def route_logic(event):
    print "Event: %s" % json.dumps(event)

    intent = event.get("currentIntent", {}).get("name", None)

    print "Intent", intent

    if intent == "GetStarted":
        return handle_get_started(event)
    elif intent == "AddChild":
        return handle_add_child(event)
    else:
        return get_unhandled_resp(event)


def handle_get_started(event):
    return {"dialogAction": {
        "type": "Close",
        "fulfillmentState": "Fulfilled",
        "message": {
            "contentType": "PlainText",
            "content": "ParentOrb can automate reminders with your child, like being ready at a certain time, chore deadlines, and curfews."
        },
        "responseCard": {
            "version": 1,
            "contentType": "application/vnd.amazonaws.card.generic",
            "genericAttachments": [
                {
                    "title": " Lets add your first child.",
                    "buttons": [
                        {
                            "text": "Add Child",
                            "value": "Add Child"
                        }
                    ]
                }
            ]
        }
    }}

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


    if source == "DialogCodeHook":

        if not getSlotVar(slots, 'child'):

            session["phone_attempts"] = 0
            session["validated_phone"] = "0"
            session["has_validated_code"] = "0"
            session["validation_code"] = ""
            session["validation_attempts"] = 0

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

                    validation_code = ''.join(random.SystemRandom().choice(['0','1','2','3','4','5','6','7','8','9']) for _ in range(5))

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

                    #add the number to the user

                    return { "dialogAction" :{
                        "type": "Close",
                        "fulfillmentState": "Fulfilled",
                        "message": {
                            "contentType": "PlainText",
                            "content": "Great, %s has been added!" %  getSlotVar(slots, 'child')
                        }
                    }, "sessionAttributes": session,}
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

def getSesVar(event, key_name):

    return event.get('sessionAttributes',{}).get(key_name, None)

def getSlotVar(slots, key_name):

    return slots.get(key_name, None)