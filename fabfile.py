import os

from fabric.api import *

from core.fb_api_wrapper import Messenger

from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentorb.settings_local")
application = get_wsgi_application()
from django.conf import settings as django_settings


@task
def fb_get_started_button():

    m = Messenger(django_settings.FB_MESSENGER_TOKEN)
    print m.get_started_button()

@task
def fb_set_started_button():

    m = Messenger(django_settings.FB_MESSENGER_TOKEN)
    print m.set_started_button("Get Started")

    fb_get_started_button()

@task
def fb_get_greeting():

    m = Messenger(django_settings.FB_MESSENGER_TOKEN)
    print m.get_getting()

@task
def fb_set_greeting():

    greeting = "ParentOrb is smart helper for parents with connected kids. Tap Get Started to begin."
    m = Messenger(django_settings.FB_MESSENGER_TOKEN)

    print m.set_greeting(greeting)

    fb_get_greeting()

