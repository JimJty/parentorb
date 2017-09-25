import hashlib
import importlib
import json
import logging
import random
import re
import traceback

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from bot.base_intent import Intent
from core.models import AppUser

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def route_logic(event):
    logger.info("Event: %s", json.dumps(event, indent=4))

    try:
        intent = event.get("currentIntent", {}).get("name", None)
        bot_name = event.get("bot", {}).get("name", None)

        intent_obj = init_intent(intent, bot_name)

        if intent_obj:
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

#helpers

def init_intent(intent_name, bot_name):

    if not intent_name:
        return None

    intent_name = convert_camelcase(intent_name)
    bot_name = convert_camelcase(bot_name)

    try:
        module = importlib.import_module("bot.%s.intents.%s" % (bot_name,intent_name))
        cls = getattr(module, 'Intent')

        obj = cls()

        return obj

    except ImportError:
        return None

def convert_camelcase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

# def getSesVar(event, key_name):
#
#     return event.get('sessionAttributes',{}).get(key_name, None)
#
# def getSlotVar(slots, key_name):
#
#     return slots.get(key_name, None)