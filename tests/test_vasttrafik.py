import sys
import types
import unittest
from datetime import datetime, timedelta, timezone

# The real credentials file is gitignored and not needed here
sys.modules['api.vasttrafik.key_and_secret'] = types.SimpleNamespace(KEY='', SECRET='')
from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi

CET = timezone(timedelta(hours=1))

def departure(platform, direction, planned, estimated, cancelled=False):
    return {
        'stopPoint': {'platform': platform},
        'serviceJourney': {'direction': direction, 'line': {
            'name': 'Spårvagn 7', 'shortName': '7', 'transportMode': 'tram',
            'foregroundColor': '#ffffff', 'backgroundColor': '#764712', 'borderColor': '#764712'}},
        'plannedTime': planned,
        'estimatedOtherwisePlannedTime': estimated,
        'isCancelled': cancelled,
    }

# Trimmed from a real answer for Chalmers on 2026-10-30. None were cancelled then, so the last one is made up.
DEPARTURES = [
    departure('B', 'Tynnered', '2026-10-30T19:10:00.0000000+01:00', '2026-10-30T19:15:00.0000000+01:00'),
    departure('A', 'Bergsjön', '2026-10-30T19:15:00.0000000+01:00', '2026-10-30T19:15:00.0000000+01:00'),
    departure('B', 'Tynnered', '2026-10-30T19:25:00.0000000+01:00', '2026-10-30T19:25:00.0000000+01:00', cancelled=True),
]

class DeparturesDictTest(unittest.TestCase):

    def test_groups_by_platform_and_line_and_parses_times(self):
        api = VasttrafikReseplanerarenApi.__new__(VasttrafikReseplanerarenApi) # Skip __init__, it loads the stops
        api.get_departures_data = lambda **kwargs: DEPARTURES

        table = api.get_departures_data_dict('Chalmers')

        self.assertEqual(sorted(table), ['A', 'B'])
        tynnered = table['B']['Spårvagn 7 Tynnered']
        self.assertEqual((tynnered['short_name'], tynnered['type'], tynnered['bg_color']), ('7', 'tram', '#764712'))
        self.assertEqual(tynnered['time'], [datetime(2026, 10, 30, 19, 10, tzinfo=CET), datetime(2026, 10, 30, 19, 25, tzinfo=CET)])
        self.assertEqual(tynnered['rt_time'], [datetime(2026, 10, 30, 19, 15, tzinfo=CET), None])
        self.assertEqual(table['A']['Spårvagn 7 Bergsjön']['rt_time'], [datetime(2026, 10, 30, 19, 15, tzinfo=CET)])

if __name__ == '__main__':
    unittest.main()
