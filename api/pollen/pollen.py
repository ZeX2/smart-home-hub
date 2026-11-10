from datetime import date
from math import cos, radians

from requests import Session
from requests.adapters import HTTPAdapter

API = 'https://api.pollenrapporten.se/v1'
TIMEOUT = 10
# From /pollen-level-definitions, fixed so it costs no request
LEVELS = ['Inga halter', 'Låga', 'Låga till måttliga', 'Måttliga', 'Måttliga till höga', 'Höga', 'Höga till mycket höga', 'Mycket höga']

def nearest_region(regions, lat, lon):
    # Longitude degrees shrink towards the north, without the scaling Kiruna could pick a region far east
    return min(regions, key=lambda r: (r['lat'] - lat)**2 + ((r['lon'] - lon) * cos(radians(lat)))**2)

def todays_levels(forecast, pollen_names, today):
    '''[(name, level)] above zero for today, highest first. Empty off-season.'''
    if forecast is None or forecast['isEndOfSeason']:
        return []
    levels = [(pollen_names.get(entry['pollenId'], '?'), entry['level']) for entry in forecast['levelSeries']
              if entry['time'][:10] == today.isoformat() and entry['level'] > 0]
    return sorted(levels, key=lambda x: -x[1])

class PollenApi():
    def __init__(self):
        self.s = Session()
        self.s.mount('https://', HTTPAdapter(max_retries=3))
        self.regions = None
        self.pollen_names = None

    def get(self, path, **params):
        response = self.s.get(f'{API}/{path}', params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()['items']

    def get_pollen(self, lat, lon):
        '''(region name, [(pollen name, level 1-7)]) for the region nearest to lat, lon.'''
        if self.regions is None:
            # 'Sverige' is the national summary, it has no levels of its own
            self.regions = [{'id': r['id'], 'name': r['name'], 'lat': float(r['latitude']), 'lon': float(r['longitude'])}
                            for r in self.get('regions') if r['name'] != 'Sverige']
        if self.pollen_names is None:
            self.pollen_names = {p['id']: p['name'] for p in self.get('pollen-types')}
        region = nearest_region(self.regions, lat, lon)
        forecasts = self.get('forecasts', region_id=region['id'], current='true')
        return region['name'], todays_levels(forecasts[0] if forecasts else None, self.pollen_names, date.today())
