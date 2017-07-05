import requests


class Messenger:
    BASE_URL = "https://graph.facebook.com/v2.9"

    def __init__(self, access_token):
        self.access_token = access_token

    def get_started_button(self):
        params = {
            "fields": "get_started",
            "access_token": self.access_token,
        }

        url = self.BASE_URL + "/me/messenger_profile"
        resp = requests.get(url, params=params)

        return resp.json()

    def set_started_button(self, payload):
        params = {"get_started": {"payload": payload}, "access_token": self.access_token}
        url = self.BASE_URL + "/me/messenger_profile"

        resp = requests.post(url, json=params)

        return resp.json()

    def get_getting(self):
        params = {"fields": "greeting", "access_token": self.access_token}
        url = self.BASE_URL + "/me/messenger_profile"

        resp = requests.get(url, params=params)

        return resp.json()

    def set_greeting(self, greeting):
        params = {"greeting": [
            {
                "locale": "default",
                "text": greeting
            }],
            "access_token": self.access_token
        }
        url = self.BASE_URL + "/me/messenger_profile"

        resp = requests.post(url, json=params)

        return resp.json()

    def get_profile(self, psid):
        params = {
            "fields": "first_name,last_name,profile_pic,locale,timezone,gender,is_payment_enabled,last_ad_referral",
            "access_token": self.access_token
        }
        url = self.BASE_URL + "/" + psid

        resp = requests.get(url, params=params)

        self._handler_error(resp)

        return resp.json()

    def send_message(self, psid, message, img_url=None):
        params = {
            "recipient": {
                "id": psid
            },
            "message": {
                "text": message
            },
            "access_token": self.access_token
        }

        url = self.BASE_URL + "/me/messages"

        resp = requests.post(url, json=params)

        if img_url:
            params["message"] = {
                "attachment": {
                    "type": "image",
                    "payload": {
                        "url": img_url
                    }
                }
            }

            resp = requests.post(url, json=params)

        return resp.json()

    def _handler_error(self, resp):
        error = resp.json().get('error', None)

        if error:
            raise FacebookException("FB API Error: %s" % error)

    def get_menu(self):
        params = {"fields": "persistent_menu", "access_token": self.access_token}
        url = self.BASE_URL + "/me/messenger_profile"

        resp = requests.get(url, params=params)

        return resp.json()

    def set_menu(self, call_to_actions):
        params = {"persistent_menu": [
            {
                "locale": "default",
                "composer_input_disabled": False,
                "call_to_actions": call_to_actions
            }],
            "access_token": self.access_token
        }
        url = self.BASE_URL + "/me/messenger_profile"

        resp = requests.post(url, json=params)

        return resp.json()


class FacebookException(Exception):
    pass
