import os
import base64
from xml.etree import ElementTree
from xml.dom import minidom
from datetime import datetime, timedelta, timezone, tzinfo

from requests import Session, Request
import requests
from requests.adapters import HTTPAdapter, SSLError

from key_and_secret import KEY, SECRET

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
STOPS_PATH = os.path.join(FILE_DIR, 'stops.xml')
TIMEOUT = 100
TOKEN_API = 'https://api.vasttrafik.se/token'
API = 'https://api.vasttrafik.se/bin/rest.exe/v2'

class VasttrafikApi():
    def __init__(self):
        self.s = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)

        self.last_updated_token = datetime.now() - timedelta(hours=2)
        self.access_token = ''
        self.token_type = ''
        self.headers = {}

        self.update_token_and_headers()

    def send(self, request):
        if datetime.now() - self.last_updated_token > timedelta(hours=1):
            self.update_token_and_headers()
        return self._send(request)

    def _send(self, request):
        try:
            response = self.s.send(request.prepare(), timeout=TIMEOUT)
        except SSLError:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = self.s.send(request.prepare(), timeout=TIMEOUT, verify=False)

        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f'Västtrafik API failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response
    
    def update_token_and_headers(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode((KEY + ":" + SECRET).encode()).decode()}'}
        data = {'grant_type': 'client_credentials'}

        request = Request('POST', TOKEN_API, headers=headers, data=data)
        data = self._send(request).json()
        self.access_token = data['access_token']
        self.token_type = data['token_type']
        self.last_updated_token = datetime.now() - timedelta(seconds=data['expires_in'])

        self.headers = {'Authorization' : f'Bearer {self.access_token}'}

class VasttrafikReseplanerarenApi(VasttrafikApi):
    def __init__(self):
        super().__init__()
    
    def get_stops(self):
        if not os.path.exists(STOPS_PATH):
            request = Request('GET', f'{API}/location.allstops', headers=self.headers)
            response = self.send(request).content
            with open(STOPS_PATH, 'w') as f:
                f.write(minidom.parseString(response).toprettyxml())
        #data = ElementTree.fromstring(response)

    def get_departures(self, stop_id, date=None, time=None):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        if not time:
            time = datetime.now().strftime('%H:%M')

        params = {'id': stop_id, 'date': date, 'time': time}
        request = Request('GET', f'{API}/departureBoard', headers=self.headers, params=params)
        print(self.send(request).content)
        data = ElementTree.fromstring(self.send(request).content)

        return data

vasttrafik_api = VasttrafikReseplanerarenApi()
vasttrafik_api.get_stops()
print(vasttrafik_api.get_departures('9022014005160001'))