import unittest
from datetime import date, datetime, timezone

from api.smhi.smhi import daily_forecast, sun_times
from api.pollen.pollen import nearest_region, todays_levels

class SunTimesTest(unittest.TestCase):

    def assertNear(self, actual, expected, minutes=3):
        self.assertLess(abs((actual - expected).total_seconds()), minutes*60, f'{actual} != {expected}')

    def test_stockholm_midsummer(self):
        # Almanac: sunrise 03:30, sunset 22:08 CEST
        sunrise, sunset = sun_times(59.3293, 18.0686, date(2026, 6, 21))
        self.assertNear(sunrise, datetime(2026, 6, 21, 1, 30, tzinfo=timezone.utc))
        self.assertNear(sunset, datetime(2026, 6, 21, 20, 8, tzinfo=timezone.utc))

    def test_kiruna_never_rises_or_sets(self):
        self.assertEqual(sun_times(67.8558, 20.2253, date(2026, 12, 21)), 'Polarnatt')
        self.assertEqual(sun_times(67.8558, 20.2253, date(2026, 6, 21)), 'Midnattssol')

class DailyForecastTest(unittest.TestCase):

    def test_groups_by_day(self):
        forecast = [
            (datetime(2026, 11, 10, 11), 5.0, 3, 0.5),
            (datetime(2026, 11, 10, 12), 7.0, 6, None),
            (datetime(2026, 11, 10, 23), 2.0, 1, 1.0),
            (datetime(2026, 11, 11, 12), 4.0, 18, 3.0),
        ]
        self.assertEqual(daily_forecast(forecast), [
            (date(2026, 11, 10), 2.0, 7.0, 6, 1.5),
            (date(2026, 11, 11), 4.0, 4.0, 18, 3.0),
        ])

class PollenTest(unittest.TestCase):

    def test_nearest_region(self):
        regions = [{'name': 'Göteborg', 'lat': 57.7, 'lon': 12.0}, {'name': 'Jönköping', 'lat': 57.77, 'lon': 14.19}]
        self.assertEqual(nearest_region(regions, 57.6, 12.4)['name'], 'Göteborg')

    def test_todays_levels(self):
        names = {'b': 'Björk', 'g': 'Gräs', 'a': 'Al'}
        forecast = {'isEndOfSeason': False, 'levelSeries': [
            {'pollenId': 'b', 'level': 2, 'time': '2026-05-01T00:00:00'},
            {'pollenId': 'g', 'level': 5, 'time': '2026-05-01T00:00:00'},
            {'pollenId': 'a', 'level': 0, 'time': '2026-05-01T00:00:00'},
            {'pollenId': 'b', 'level': 7, 'time': '2026-05-02T00:00:00'},
        ]}
        self.assertEqual(todays_levels(forecast, names, date(2026, 5, 1)), [('Gräs', 5), ('Björk', 2)])
        self.assertEqual(todays_levels({'isEndOfSeason': True, 'levelSeries': []}, names, date(2026, 5, 1)), [])
        self.assertEqual(todays_levels(None, names, date(2026, 5, 1)), [])

if __name__ == '__main__':
    unittest.main()
