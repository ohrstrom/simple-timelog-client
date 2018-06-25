
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

        try:
            token = data.get('key')
            return token
        except:
            raise TimelogClientAPIException('bad credentials')

    def log(self, *args, **kwargs):

        url = '{}/api/v1/timelog/entry/'.format(self.endpoint)
        payload = kwargs

        r = requests.post(url, data=payload, headers=self.headers)

        data = r.json()

        return data


    def attendance(self, status, timestamp=None):

        url = '{}/api/v1/timelog/attendance/'.format(self.endpoint)

        # check for last state
        r = requests.get(url, headers=self.headers)
        data = r.json()

        if data['results'] and data['results'][0]['status'] == status:
            print('no status change - skip...')
            return data['results'][0]


        payload = {
            'timestamp': timestamp,
            'status': status,
        }

        r = requests.post(url, data=payload, headers=self.headers)

        data = r.json()

        return data


    def report(self, date_start=None, date_end=None):

        # ?date_after=2018-05-22&date_before=2018-05-22

        log_url = '{}/api/v1/timelog/entry/'.format(self.endpoint)
        attendance_url = '{}/api/v1/timelog/attendance/'.format(self.endpoint)

        payload = {}
        if date_start:
            payload['date_after'] = date_start

        if date_end:
            payload['date_before'] = date_end

        log_r = requests.get(log_url, params=payload, headers=self.headers)
        attendance_r = requests.get(attendance_url, params=payload, headers=self.headers)

        return log_r.json(), attendance_r.json()
