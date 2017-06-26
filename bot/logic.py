import json

from django.conf import settings
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
            session["validated_phone"] = False

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

            validated_phone = session.get("validated_phone", False)
            phone_number = getSlotVar(slots, 'phone_number')

            if not validated_phone and phone_number:
                client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)

                try:
                    resp = client.lookups.phone_numbers(phone_number).fetch()

                    session["validated_phone"] = True
                    slots["phone_number"] = resp.phone_number

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