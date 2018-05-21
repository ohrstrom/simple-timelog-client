
import requests
from .exceptions import TimelogClientAPIException

class TimelogClient(object):

    def __init__(self, endpoint, token=None):
        self.endpoint = endpoint
        self.token = token
        self.headers = {
            'Authorization': 'Token {}'.format(self.token),
        }

    def login(self, email, password):
        # raise TimelogClientAPIException('bad credentials')

        url = '{}/api/auth/login/'.format(self.endpoint)
        payload = {
            'email': email,
            'password': password,
        }

        r = requests.post(url, data=payload)

        data = r.json()

        print(data)

        try:
            token = data.get('key')
            return token
        except:
            raise TimelogClientAPIException('bad credentials')

    def log(self, *args, **kwargs):

        url = '{}/api/v1/timelog/entry/'.format(self.endpoint)
        payload = kwargs

        r = requests.post(url, data=payload, headers=self.headers)

        print(r.text)

        data = r.json()

        print(data)
        pass
