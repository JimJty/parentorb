import json

from core.models import AppUser


def route_logic(event):
    print "Event: %s" % json.dumps(event)

    intent = event.get("currentIntent", {}).get("name", None)

    print "Intent", intent

    if intent == "GetStarted":
        return handle_get_started(event)
    else:

        return {"dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
                "contentType": "PlainText",
                "content": "ParentOrb couldn't handle your request. Please try starting again."
            },
        }}


def handle_get_started(event):
    return {"dialogAction": {
        "type": "Close",
        "fulfillmentState": "Fulfilled",
        "message": {
            "contentType": "PlainText",
            "content": "ParentOrb can automate reminders with your child, like being ready at a certain time, chore deadlines, and curfews. Lets add your first child."
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
