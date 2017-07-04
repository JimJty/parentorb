# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import boto3
from django.conf import settings
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render

import logging

from django.views.decorators.csrf import csrf_exempt
from twilio.request_validator import RequestValidator

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def home(request):
    context = {

    }

    return render(request, 'front/home.html', context)

@csrf_exempt
def handle_twilio(request):

    #validate
    validator = RequestValidator(settings.TWILIO_KEY)

    print(validator.validate(
        request.build_absolute_uri(),
        request.POST,
        request.META.get('HTTP_X_TWILIO_SIGNATURE', ''))
    )

    msg = None

    results = {'status':1 if not msg else 0,"msg":msg,}


    return HttpResponse(json.dumps(results), content_type='application/javascript')


def error_test(request):

    raise Exception("forcing error")

