from django.conf.urls import  url

from website.views import home, error_test, handle_twilio, privacy, contact

urlpatterns = [

    url(r'^$', home, name='home'),

    url(r'^privacy/$', privacy, name='privacy'),

    url(r'^contact/$', contact, name='contact'),

    url(r'^handle-twilio/$', handle_twilio, name="hanlde-twilio"),

    url(r'^error-test/$', error_test, name="error-test"),


]