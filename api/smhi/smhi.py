import os
from datetime import datetime, timedelta, timezone

from requests import Session, Request
from requests.adapters import HTTPAdapter

WSYMB2_MEANING = [
    'Klart',
    'Lätt molnighet',
    'Halvklart',
    'Molnigt',
    'Mycket moln',
    'Mulet',
    'Dimma',
    'Lätt regnskur',
    'Regnskur',
    'Kraftig regnskur',
    'Åskskur',
    'Lätt by av regn och snö',
    'By av regn och snö',
    'Kraftig by av regn och snö',
    'Lätt snöby',
    'Snöby',
    'Kraftig snöby',
    'Lätt regn',
    'Regn',
    'Kraftigt regn',
    'Åska',
    'Lätt snöblandat regn',
    'Snöblandat regn',
    'Kraftigt snöblandat regn',
    'Lätt snöfall',
    'Snöfall',
    'Ymnigt snöfall'
]
SMHI_DIR = os.path.dirname(os.path.realpath(__file__))
TIMEOUT = 10

class SMHIApi():
    def __init__(self):
        self.s = Session()
        adapter = HTTPAdapter(max_retries=3)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)

    def get_request_data(self, request):
        response = self.s.send(request.prepare(), timeout=TIMEOUT)
        if response.status_code != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f'{self.__class__.__name__} failed for url {request.url}! {response.status_code}! \n Response text: {response.text}')
        else:
            return response.json()

class SMHIForecastApi(SMHIApi):
    def __init__(self):
        super().__init__()
        self.API = 'http://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2'
        # See https://opendata.smhi.se/apidocs/metfcst/index.html for more info!

    def get_wsymb2_path(self, value):
        return os.path.join(SMHI_DIR, 'wsymb2', str(value))

    def get_wsymb2_meaning(self, value):
        return WSYMB2_MEANING[int(value)-1]

    def get_parameters(self):
        request = Request('GET', f'{self.API}/parameter.json')
        data = self.get_request_data(request)
        return data['parameter']
    
    def get_point_weather_data(self, lat, lon, *parameters):
        request = Request('GET', f'{self.API}/geotype/point/lon/{lon}/lat/{lat}/data.json')
        data = self.get_request_data(request)

        weather_data = []
        for point_data in data['timeSeries']:
            time = point_data['validTime']
            time = datetime.fromisoformat(time.replace('Z', '+00:00'))
            time = time.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)

            data = dict.fromkeys(parameters)
            for parameter_data in point_data['parameters']:
                if parameter_data['name'] in parameters:
                    data[parameter_data['name']] = parameter_data['values'][0]
            
            weather_data.append(tuple((time, *data.values())))

        return weather_data

    def get_temperatures(self, lat, lon):
        return self.get_point_weather_data(lat, lon, 't', 'Wsymb2')

class SMHIObservationApi(SMHIApi):
    def __init__(self):
        super().__init__()
        self.API = 'http://opendata-download-metobs.smhi.se/api/version/latest'

    def get_parameters(self):
        request = Request('GET', f'{self.API}.json')
        data = self.get_request_data(request)

        parameters = []
        for parameter_data in data['resource']:
            parameter = (parameter_data['key'], parameter_data['title'], parameter_data['summary'])
            parameters.append(parameter)
        parameters = sorted(parameters, key=lambda x: int(x[0]))

        return parameters

    def get_stations(self, parameter, only_new_stations=True):
        request = Request('GET', f'{self.API}/parameter/{parameter}.json')
        data = self.get_request_data(request)

        stations = []
        for station_data in data['station']:
            # Ensure active measuring station
            if only_new_stations:
                if not station_data['active']:
                    continue

                # Ensure measurements at most 24 hours old
                last_updated = datetime.fromtimestamp(station_data['updated']/1000)
                now = datetime.now()
                if now-last_updated > timedelta(days=1):
                    continue

            station = (station_data['key'], station_data['name'])
            stations.append(station)
        stations = sorted(stations, key=lambda x: x[1])

        return stations

    def get_temperatures(self, station_id, period):
        periods = {'hour': 'latest-hour', 'day': 'latest-day', 'months': 'latest-months', 'archive': 'corrected-archive'}
        period = periods[period]

        request = Request('GET', f'{self.API}/parameter/1/station/{station_id}/period/{period}/data.json')
        data = self.get_request_data(request)

        temperatures = []
        for temperature_data in data['value']:
            temperature = (temperature_data['date']/1000, temperature_data['value'])
            temperatures.append(temperature)
        temperatures = sorted(temperatures, key=lambda x: int(x[0]))

        return temperatures


#print(SMHIObservationApi().get_parameters())
#print(len(SMHIObservationApi().get_stations(1)))
#print(SMHIObservationApi().get_temperatures(71420, 'day'))
#print([(datetime.fromtimestamp(x[0]), x[1]) for x in SMHIObservationApi().get_temperatures(71420, 'hour')])

#print(SMHIForecastApi().get_parameters())
#temps = SMHIForecastApi().get_temperatures(57.71667, 12)
#print(temps)
