import json

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
    session = event.get("sessionAttributes",{})


    if source == "DialogCodeHook":

        if not getSlotVar(slots, 'child'):
            return {"dialogAction": {
                "type": "Delegate",
                "slots": slots,
            }}

        elif not getSlotVar(slots, 'phone_number'):
            return {"dialogAction": {
                "type": "Delegate",
                "slots": slots,
            }}

            # return { "dialogAction" :{
            #     "type": "ElicitSlot",
            #     "message": {
            #         "contentType": "PlainText",
            #         "content": "The phone number appears to be invalid, try entering just numbers."
            #     },
            #     "intentName": intent,
            #     "slots": slots,
            #     "slotToElicit": "phone_number",
            # }}

        else:
            return {"dialogAction": {
                "type": "Delegate",
                "slots": slots,
            }}



    return get_unhandled_resp(event)


#helpers

def getSesVar(event, key_name):

    return event.get('sessionAttributes',{}).get(key_name, None)

def getSlotVar(slots, key_name):

    return slots.get(key_name, None)