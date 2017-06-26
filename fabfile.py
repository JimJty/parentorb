import os

from fabric.api import *
from os.path import dirname
from twilio.rest import Client

from core.fb_api_wrapper import Messenger

from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentorb.settings_local")
application = get_wsgi_application()
from django.conf import settings as django_settings

env.use_ssh_config = True

BASE_DIR = dirname(env.real_fabfile)

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

@task
def deploy_bot():

    env.host_string = django_settings.DEPLOY_ENV

    proj_path = "~/src/parentorb"

    with lcd(BASE_DIR):
        local("git push")

    with cd("%s" % proj_path) :
        run("pwd")
        run("git pull")

        run('source ../env2/bin/activate && pip install -r requirements.txt')

        run('source ../env2/bin/activate && zappa update devbot')


@task
def deploy_website():

    env.host_string = django_settings.DEPLOY_ENV

    proj_path = "~/src/parentorb"

    with lcd(BASE_DIR):
        local("git push")

    with cd("%s" % proj_path) :
        run("pwd")
        run("git pull")

        run('source ../env2/bin/activate && pip install -r requirements.txt')

        run('source ../env2/bin/activate && zappa update prod')

@task
def send_sms(number):

    #testing twilio

    client = Client(django_settings.TWILIO_ACCOUNT, django_settings.TWILIO_KEY)

    message = client.messages.create(to=number, from_=django_settings.TWILIO_FROM_NUMBER, body="Hello!")

    print message

@task
def lookup_number(number):

    #testing twilio

    client = Client(django_settings.TWILIO_ACCOUNT, django_settings.TWILIO_KEY)

    resp = client.lookups.phone_numbers(number).fetch()

    print resp.country_code, resp.phone_number
