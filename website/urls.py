from django.conf.urls import  url

from website.views import home, error_test, handle_twilio

urlpatterns = [

    url(r'^$', home, name='home'),

    url(r'^handle-twilio/$', handle_twilio, name="hanlde-twilio"),

    url(r'^error-test/$', error_test, name="error-test"),


]