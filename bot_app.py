import os
from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentorb.settings_prod")
application = get_wsgi_application() #init django, for models

from bot.logic import route_logic

def handler(event, context):

    return route_logic(event)


