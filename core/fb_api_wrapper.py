import requests


class Messenger:
    BASE_URL = "https://graph.facebook.com/v2.9/me/messenger_profile"

    def __init__(self, access_token):
        self.access_token = access_token
        self.request_url = "%s?access_token=%s" % (self.BASE_URL, access_token)

    def get_started_button(self):
        params = {"fields": "get_started"}
        resp = requests.get(self.request_url, params=params)

        return resp.json()

    def set_started_button(self, payload):
        params = {"get_started": {"payload": payload}}
        resp = requests.post(self.request_url, json=params)

        return resp.json()

    def get_getting(self):
        params = {"fields": "greeting"}
        resp = requests.get(self.request_url, params=params)

        return resp.json()

    def set_greeting(self, greeting):
        params = {"greeting":[
            {
                "locale": "default",
                "text": greeting
            }]
        }

        resp = requests.post(self.request_url, json=params)

        return resp.json()
