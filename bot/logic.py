from core.models import AppUser


def route_logic(event):

    print "Event: %s" % event

    print "App User Count: %s" % AppUser.objects.count()

    return {"dialogAction": {
        "type": "Close",
        "fulfillmentState": "Fulfilled",
        "message": {
            "contentType": "PlainText",
            "content": "Thanks, your pizza has been ordered."
        },
    }}