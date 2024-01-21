import os
import json
import base64
from datetime import datetime, timedelta

import pandas as pd
from requests import Session, Request
from requests.adapters import HTTPAdapter, SSLError

from .key_and_secret import KEY, SECRET

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
STOPS_PATH_JSON = os.path.join(FILE_DIR, 'stops.json')
TIMEOUT = 100
TOKEN_API = 'https://ext-api.vasttrafik.se/token'
API = 'https://ext-api.vasttrafik.se/pr/v4'
GEO_API = 'https://ext-api.vasttrafik.se/geo/v2'

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
                raise Exception(f'{self.__class__.__name__} failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
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
            request = Request('GET', f'{GEO_API}/StopPoints', headers=self.headers)
            data = self.send(request).json()
            data = data['stopPoints']

            data = list({elem['gid']: elem for elem in data}.values())

            with open(STOPS_PATH_JSON, 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))

        try:
            with open(STOPS_PATH_JSON, encoding='utf-8') as f:
                stop_locations = json.load(f)
        except:
            get_stops_data()
            with open(STOPS_PATH_JSON, encoding='utf-8') as f:
                stop_locations = json.load(f)

        last_modified = datetime.fromtimestamp(os.path.getmtime(STOPS_PATH_JSON))

        if datetime.now() - last_modified > timedelta(weeks=1):
            get_stops_data()
            with open(STOPS_PATH_JSON, encoding='utf-8') as f:
                stop_locations = json.load(f)

        self.stops_data = ((stop_location['name'], stop_location['stopAreaGid']) for stop_location in stop_locations)
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
            track = departure['stopPoint']['platform']
            if track not in departures_table:
                departures_table[track] = dict()

            tram = f'{departure["serviceJourney"]["line"]["name"]} {departure["serviceJourney"]["direction"]}'
            if tram not in departures_table[track]:
                departures_table[track][tram] = dict()
                departures_table[track][tram]['name'] = departure['serviceJourney']['line']['name']
                departures_table[track][tram]['short_name'] = departure['serviceJourney']['line']['shortName']
                departures_table[track][tram]['type'] = departure['serviceJourney']['line']['transportMode']
                departures_table[track][tram]['direction'] = departure['serviceJourney']['direction']
                departures_table[track][tram]['fg_color'] = departure['serviceJourney']['line']['foregroundColor']
                departures_table[track][tram]['bg_color'] = departure['serviceJourney']['line']['backgroundColor']
                departures_table[track][tram]['stroke'] = departure['serviceJourney']['line']['borderColor']
                departures_table[track][tram]['time'] = []
                departures_table[track][tram]['rt_time'] = []

            time = datetime.fromisoformat(departure['plannedTime'][:19] + departure['plannedTime'][27:])
            if departure['isCancelled']:
                rt_time = None
            else:
                rt_time = datetime.fromisoformat(departure['estimatedOtherwisePlannedTime'][:19] + departure['estimatedOtherwisePlannedTime'][27:])
            departures_table[track][tram]['time'].append(time)
            departures_table[track][tram]['rt_time'].append(rt_time)
        
        return departures_table

    def get_departures_data(self, stop_id=None, stop_name=None, time_span_minutes=None):
        if stop_name:
            stop_id = self.get_stop_id(stop_name)

        return self._get_departures_data(stop_id, time_span_minutes)

    def _get_departures_data(self, stop_id, time_span_minutes=None):
        params = {'stopPointGid': stop_id, 'timeSpanInMinutes': time_span_minutes, 'limit': 1000, 'maxDeparturesPerLineAndDirection': 10}
        request = Request('GET', f'{API}/stop-areas/{stop_id}/departures', headers=self.headers, params=params)
        data = self.send(request).json()['results']

        return data

    def get_live_map_vehicles(self, minx, maxx, miny, maxy, limit=200):
        params = {'lowerLeftLong': minx, 'upperRightLong': maxx, 'lowerLeftLat': miny, 'upperRightLat': maxy, 'limit': limit}
        request = Request('GET', f'{API}/positions', headers=self.headers, params=params)
        data = self.send(request).json()['livemap']['vehicles']

        return data
