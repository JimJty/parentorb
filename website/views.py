# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import boto3
from django.core.mail import EmailMessage
from django.shortcuts import render

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def home(request):
    context = {

    }

    email = EmailMessage('Hi!', 'Cool message for Joe', 'support@parentorb.com', ['jimr3110@gmail.com'])
    email.send()

    return render(request, 'front/home.html', context)

def error_test(request):

    raise Exception("forcing error")

