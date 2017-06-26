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

    return render(request, 'front/home.html', context)

def error_test(request):

    raise Exception("forcing error")

