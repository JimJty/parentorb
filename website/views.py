# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import boto3
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def home(request):
    context = {

    }

    return render(request, 'front/home.html', context)

def handle_twilio(request):

    print request.POST

    msg = None

    results = {'status':1 if not msg else 0,"msg":msg,}


    return HttpResponse(json.dumps(results), content_type='application/javascript')


def error_test(request):

    raise Exception("forcing error")

