import os
from datetime import date, datetime, timedelta, timezone
from math import acos, asin, cos, degrees, radians, sin

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
        self.API = 'https://opendata-download-metfcst.smhi.se/api/category/snow1g/version/1'
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
            time = point_data['time']
            time = datetime.fromisoformat(time.replace('Z', '+00:00'))
            time = time.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)

            entry = dict.fromkeys(parameters)
            for param in parameters:
                if param in point_data['data']:
                    entry[param] = point_data['data'][param]

            weather_data.append(tuple((time, *entry.values())))

        return weather_data

    def get_temperatures(self, lat, lon):
        return self.get_point_weather_data(lat, lon, 'air_temperature', 'symbol_code')

    def get_forecast(self, lat, lon):
        '''[(local time, temp, symbol, precipitation mm)], hourly at first, then 6-, 12- and 24-hourly.'''
        return self.get_point_weather_data(lat, lon, 'air_temperature', 'symbol_code', 'precipitation_amount_mean')

def daily_forecast(forecast):
    '''[(date, min temp, max temp, symbol, precipitation mm)] per day, symbol from the time nearest noon.'''
    days = {}
    for entry in forecast:
        days.setdefault(entry[0].date(), []).append(entry)
    daily = []
    for day, entries in days.items():
        temps = [e[1] for e in entries]
        noon = min(entries, key=lambda e: abs(e[0].hour - 12))
        # shortcut: amounts are summed per period end, so a 24 h period late in the forecast lands on one day, fine for a daily glance
        daily.append((day, min(temps), max(temps), noon[2], sum(e[3] or 0 for e in entries)))
    return daily

def sun_times(lat, lon, day):
    '''(sunrise, sunset) as UTC datetimes, or 'Midnattssol' / 'Polarnatt' when the sun never sets or rises.
    The sunrise equation, see https://en.wikipedia.org/wiki/Sunrise_equation'''
    n = day.toordinal() - date(2000, 1, 1).toordinal()
    j_star = n - lon/360
    m = radians((357.5291 + 0.98560028*j_star) % 360)
    c = 1.9148*sin(m) + 0.02*sin(2*m) + 0.0003*sin(3*m)
    ecliptic_lon = radians((degrees(m) + c + 180 + 102.9372) % 360)
    j_transit = j_star + 0.0053*sin(m) - 0.0069*sin(2*ecliptic_lon)
    declination = asin(sin(ecliptic_lon)*sin(radians(23.4397)))
    # -0.833° accounts for refraction and the sun's radius
    cos_hour_angle = (sin(radians(-0.833)) - sin(radians(lat))*sin(declination)) / (cos(radians(lat))*cos(declination))
    if cos_hour_angle < -1:
        return 'Midnattssol'
    if cos_hour_angle > 1:
        return 'Polarnatt'
    half_day = degrees(acos(cos_hour_angle))/360
    j2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    return j2000 + timedelta(days=j_transit - half_day), j2000 + timedelta(days=j_transit + half_day)

def sun_text(lat, lon, day):
    times = sun_times(lat, lon, day)
    if isinstance(times, str):
        return times
    return '  '.join(f'{arrow} {t.astimezone():%H:%M}' for arrow, t in zip('↑↓', times))

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
