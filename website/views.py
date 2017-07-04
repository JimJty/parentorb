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

    is_valid = validator.validate(
        request.build_absolute_uri(),
        request.POST,
        request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
    )

    msg = None

    if not is_valid:
        msg = "invalid"

    else:

        print request.POST

        lex_client = boto3.client('lex-runtime')

        user_id = request.POST.get('From', None)
        if not user_id:
            raise Exception("missing_user_id")

        user_id = user_id.replace("+","")

        msg = request.POST.get('Body', None)
        if not msg:
            msg = "hello"

        photo_url = request.POST.get('MediaUrl0',None)
        session = None
        if photo_url:
            session = {
                "photo_url": photo_url,
            }

        resp = lex_client.post_text(
            botName=settings.CHILD_BOT_NAME,
            botAlias=settings.CHILD_BOT_ALIAS,
            userId=user_id,
            sessionAttributes=session,
            inputText=msg
        )

        print resp


    results = {'status':1 if not msg else 0,"msg":msg,}


    return HttpResponse(json.dumps(results), content_type='application/javascript')


def error_test(request):

    raise Exception("forcing error")

