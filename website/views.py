# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import boto3
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render

import logging

from twilio.rest import Client

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def home(request):
    context = {

    }

    print "Testing"

    client = Client(settings.TWILIO_ACCOUNT, settings.TWILIO_KEY)

    resp = client.lookups.phone_numbers("6027226814").fetch()

    print resp.country_code, resp.phone_number

    return render(request, 'front/home.html', context)

def error_test(request):

    raise Exception("forcing error")

