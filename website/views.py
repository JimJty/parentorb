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
from twilio.rest import Client

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def home(request):
    context = {

    }

    return render(request, 'website/home.html', context)

def privacy(request):
    context = {

    }

    return render(request, 'website/privacy.html', context)

@csrf_exempt
def contact(request):

    name = request.POST.get('name',None)
    email = request.POST.get('email',None)
    message = request.POST.get('message',None)

    if message:
        msg = "Name: %s" % name
        msg += "\n\nEmail: %s" % email
        msg += "\n\nMsg: %s" % message

        email = EmailMessage("ContactForm", msg, settings.SERVER_EMAIL, (settings.SERVER_EMAIL,))
        email.send()


    return HttpResponse("", content_type='text/xml')

@csrf_exempt
def handle_twilio(request):

    #uncomment out for testing
    #resp_message = "<Response></Response>"
    #return HttpResponse(resp_message, content_type='text/xml')

    #validate
    validator = RequestValidator(settings.TWILIO_KEY)

    is_valid = validator.validate(
        request.build_absolute_uri(),
        request.POST,
        request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
    )

    resp_message = None

    if is_valid:

        lex_client = boto3.client('lex-runtime')

        user_id = request.POST.get('From', None)
        if not user_id:
            raise Exception("missing_user_id")

        user_id = user_id.replace("+","")

        msg_request = request.POST.get('Body', None)
        if not msg_request:
            msg_request = "hello"

        photo_url = request.POST.get('MediaUrl0',None)
        session = {}
        if photo_url:
            session = {
                "photo_url": photo_url,
            }

        resp = lex_client.post_text(
            botName=settings.CHILD_BOT_NAME,
            botAlias=settings.CHILD_BOT_ALIAS,
            userId=user_id,
            sessionAttributes=session,
            inputText=msg_request
        )

        #print resp
        resp_message = resp.get("message", None)
        resp_state = resp.get("dialogState", None)
        resp_session = resp.get("sessionAttributes",None)

        if resp_message and resp_state == "ElicitIntent" and not resp_session:
            resp = lex_client.post_text(
                botName=settings.CHILD_BOT_NAME,
                botAlias=settings.CHILD_BOT_ALIAS,
                userId=user_id,
                sessionAttributes=session,
                inputText="hello"
            )

            #print resp
            resp_message = resp.get("message", None)


    if resp_message:
        resp_message = "<Response><Message>%s</Message></Response>" % resp_message
    else:
        resp_message = "<Response></Response>"

    return HttpResponse(resp_message, content_type='text/xml')


def error_test(request):

    raise Exception("forcing error")

