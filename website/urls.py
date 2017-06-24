from django.conf.urls import  url

from website.views import home, error_test

urlpatterns = [

    url(r'^$', home, name='home'),
    url(r'^error-test/$', error_test, name="error-test"),

]