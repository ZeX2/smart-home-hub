import unittest

from widgets.manage_home.manage_home_widget import merge_event, is_active, air_label, batteries, battery_icon

class ManageHomeStateTest(unittest.TestCase):

    def setUp(self):
        self.states = {
            'lamp': {'isOn': False, 'lightLevel': 50, 'isReachable': True},
            'door': {'isOpen': False, 'batteryPercentage': 80, 'isReachable': True},
            'remote': {'batteryPercentage': 9, 'isReachable': True},
            'remote_half': {'batteryPercentage': 9, 'isReachable': True},
        }
        self.names = {'lamp': 'Taklampa', 'door': 'Sensor dörr', 'remote': 'Fjärrkontroll kök', 'remote_half': ''}

    def test_event_merges_only_changed_attributes(self):
        self.assertEqual(merge_event(self.states, {'id': 'lamp', 'attributes': {'isOn': True}}), 'lamp')
        self.assertEqual(self.states['lamp'], {'isOn': True, 'lightLevel': 50, 'isReachable': True})

    def test_event_updates_reachability(self):
        merge_event(self.states, {'id': 'lamp', 'isReachable': False})
        self.assertFalse(self.states['lamp']['isReachable'])

    def test_unknown_device_is_ignored(self):
        self.assertIsNone(merge_event(self.states, {'id': 'scene-1', 'attributes': {'isOn': True}}))
        self.assertIsNone(merge_event(self.states, {}))

    def test_door_is_active_when_open(self):
        self.assertFalse(is_active('openCloseSensor', self.states['door']))
        merge_event(self.states, {'id': 'door', 'attributes': {'isOpen': True}})
        self.assertTrue(is_active('openCloseSensor', self.states['door']))

    def test_air_label_skips_missing_values(self):
        self.assertEqual(air_label({'currentTemperature': 21.44, 'currentRH': 45, 'currentPM25': 3, 'vocIndex': None}),
                         '21.4°  45%  PM2.5 3')
        self.assertEqual(air_label({}), '')

    def test_batteries_lists_all_emptiest_first_and_skips_unnamed(self):
        self.assertEqual(batteries(self.states, self.names), [('Fjärrkontroll kök', 9), ('Sensor dörr', 80)])

    def test_battery_icon_follows_lowest_level(self):
        self.assertEqual(battery_icon([]), 'battery_ok.svg')
        self.assertEqual(battery_icon([('a', 80), ('b', 21)]), 'battery_ok.svg')
        self.assertEqual(battery_icon([('a', 80), ('b', 20)]), 'battery_half.svg')
        self.assertEqual(battery_icon([('a', 11), ('b', 10)]), 'battery_low.svg')

if __name__ == '__main__':
    unittest.main()
