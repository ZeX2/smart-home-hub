import os
import base64
from xml.etree import ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta

import pandas as pd
from requests import Session, Request
from requests.adapters import HTTPAdapter, SSLError

from .key_and_secret import KEY, SECRET

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
        self.stops_data = None

        self.set_stops_data()
    
    def set_stops_data(self):
        def get_stops_data():
            request = Request('GET', f'{API}/location.allstops', headers=self.headers)
            response = self.send(request).content
            data = ET.fromstring(response)
            for stop in data.findall('StopLocation'):
                if 'track' in stop.attrib:
                    data.remove(stop)
            with open(STOPS_PATH, 'w', encoding='utf-8') as f:
                f.write(minidom.parseString(ET.tostring(data)).toprettyxml())

        try:
            stop_locations = ET.parse(STOPS_PATH).getroot()
        except:
            get_stops_data()
            stop_locations = ET.parse(STOPS_PATH).getroot()

        date = stop_locations.attrib['serverdate']
        time = stop_locations.attrib['servertime']
        last_modified = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')

        if datetime.now() - last_modified > timedelta(weeks=1):
            get_stops_data()
            stop_locations = ET.parse(STOPS_PATH).getroot()

        self.stops_data = ((stop_location.attrib['name'], stop_location.attrib['id']) for stop_location in stop_locations)
        self.stops_data = pd.DataFrame(self.stops_data, columns=['name', 'id'])
        self.stops_data.set_index('id', inplace=True)

    def get_stop_names(self):
        return list(self.stops_data['name'])

    def get_stop_id(self, stop_name):
        return self.stops_data.loc[self.stops_data['name'] == stop_name].index[0]

    def get_departure_table(self, stop_name):
        departures_data = self.get_departures_data(stop_name=stop_name, time_span_minutes=60)
        departures_table = dict()

        for departure in departures_data:
            track = departure.attrib['track']
            if track not in departures_table:
                departures_table[track] = dict()

            tram = f'{departure.attrib["name"]} {departure.attrib["direction"]}'
            if tram not in departures_table[track]:
                departures_table[track][tram] = dict()
                departures_table[track][tram]['name'] = departure.attrib['name']
                departures_table[track][tram]['short_name'] = departure.attrib['sname']
                departures_table[track][tram]['type'] = departure.attrib['type']
                departures_table[track][tram]['direction'] = departure.attrib['direction']
                departures_table[track][tram]['fg_color'] = departure.attrib['fgColor']
                departures_table[track][tram]['bg_color'] = departure.attrib['bgColor']
                departures_table[track][tram]['stroke'] = departure.attrib['stroke']
                departures_table[track][tram]['time'] = []
                departures_table[track][tram]['rt_time'] = []

            time = datetime.strptime(f'{departure.attrib["date"]} {departure.attrib["time"]}', '%Y-%m-%d %H:%M')
            if 'cancelled' in departure.attrib:
                rt_time = None
            elif 'rtDate' not in departure.attrib or 'rtTime' not in departure.attrib:
                rt_time = time
            else:
                rt_time = datetime.strptime(f'{departure.attrib["rtDate"]} {departure.attrib["rtTime"]}', '%Y-%m-%d %H:%M')
            departures_table[track][tram]['time'].append(time)
            departures_table[track][tram]['rt_time'].append(rt_time)
        
        return departures_table

    def get_departures_data(self, stop_id=None, stop_name=None, date=None, time=None, time_span_minutes=None):
        if stop_name:
            stop_id = self.get_stop_id(stop_name)

        return self._get_departures_data(stop_id, date, time, time_span_minutes)

    def _get_departures_data(self, stop_id, date=None, time=None, time_span_minutes=None):
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        if not time:
            time = datetime.now().strftime('%H:%M')

        params = {'id': stop_id, 'date': date, 'time': time, 'timeSpan': time_span_minutes}
        request = Request('GET', f'{API}/departureBoard', headers=self.headers, params=params)
        data = ET.fromstring(self.send(request).content)

        return data
