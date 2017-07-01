import importlib
import inspect
import os
from django.core.wsgi import get_wsgi_application
from zappa.async import task

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentorb.settings_prod")
application = get_wsgi_application() #init django, for models

from bot.logic import route_logic

def handler(event, context):

    #for manual commands
    if event.get('command', None):
        whole_function = event['command']
        app_function = import_module_and_get_function(whole_function)
        result = run_function(app_function, event, context)
        print("Result of %s:" % whole_function)
        print(result)
        return result

    #else route to bot
    return route_logic(event)


def import_module_and_get_function(whole_function):
    """
    Given a modular path to a function, import that module
    and return the function.
    """
    module, function = whole_function.rsplit('.', 1)
    app_module = importlib.import_module(module)
    app_function = getattr(app_module, function)
    return app_function

def run_function(app_function, event, context):
    """
    Given a function and event context,
    detect signature and execute, returning any result.
    """
    args, varargs, keywords, defaults = inspect.getargspec(app_function)
    num_args = len(args)
    if num_args == 0:
        result = app_function(event, context) if varargs else app_function()
    elif num_args == 1:
        result = app_function(event, context) if varargs else app_function(event)
    elif num_args == 2:
        result = app_function(event, context)
    else:
        raise RuntimeError("Function signature is invalid. Expected a function that accepts at most "
                           "2 arguments or varargs.")
    return result