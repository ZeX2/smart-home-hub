import os
import sys
import json
import types
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone

try:
    from PySide6 import QtCore, QtGui, QtWidgets # type: ignore
except:
    from PySide2 import QtCore, QtGui, QtWidgets # type: ignore

# The real credentials file is gitignored and not needed here
sys.modules['api.vasttrafik.key_and_secret'] = types.SimpleNamespace(KEY='', SECRET='')
from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi
from widgets.vasttrafik.departures_widget import VasttrafikDeparturesWidget

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

class PinnedStopsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.config_path = os.path.join(tmp_dir.name, 'config.json')
        for patch in (mock.patch('widgets.vasttrafik.departures_widget.CONFIG_PATH', self.config_path),
                      mock.patch('widgets.vasttrafik.departures_widget.get_thread_pool')):  # no departure fetches
            patch.start()
            self.addCleanup(patch.stop)
        self.reseplaneraren = mock.Mock()
        self.reseplaneraren.get_stop_names.return_value = {'Chalmers', 'Brunnsparken', 'Korsvägen'}

    def press(self, widget, key, text=''):
        # Real key events, like the virtual keyboard sends
        for event_type in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
            QtWidgets.QApplication.sendEvent(widget.search_bar, QtGui.QKeyEvent(event_type, key, QtCore.Qt.NoModifier, text))

    def shown_results(self, widget):
        model = widget.search_bar.completer().completionModel()
        return [model.index(row, 0).data() for row in range(model.rowCount())]

    def search(self, widget, text):
        widget.search_bar.setText('x')
        self.press(widget, QtCore.Qt.Key_Backspace) # Emptied by hand, as typing is what updates the results
        for char in text:
            self.press(widget, 0, char)
        return self.shown_results(widget)

    def test_pinned_stops_stay_on_top_of_the_results(self):
        widget = VasttrafikDeparturesWidget(self.reseplaneraren)
        self.assertEqual(self.search(widget, ''), ['Chalmers'])
        self.assertEqual(self.search(widget, 'n'), ['Chalmers', 'Brunnsparken', 'Korsvägen'])
        self.assertEqual(self.search(widget, 'KORS'), ['Chalmers', 'Korsvägen'])

        widget.search_bar.setText('Korsvägen')
        widget.toggle_pin()
        self.assertEqual(self.search(widget, ''), ['Chalmers', 'Korsvägen'])
        self.assertEqual(self.search(widget, 'brunn'), ['Chalmers', 'Korsvägen', 'Brunnsparken'])

        widget.show_pinned_stops() # The list icon, with a search typed
        self.assertEqual(self.shown_results(widget), ['Chalmers', 'Korsvägen'])

    def test_names_starting_with_the_search_come_first(self):
        self.reseplaneraren.get_stop_names.return_value = {'Chalmers', 'Antens kapell', 'Kapellsgatan', 'Kapellplatsen'}
        widget = VasttrafikDeparturesWidget(self.reseplaneraren)
        self.assertEqual(self.search(widget, 'kapell'), ['Chalmers', 'Kapellplatsen', 'Kapellsgatan', 'Antens kapell'])

    def test_pins_are_remembered(self):
        widget = VasttrafikDeparturesWidget(self.reseplaneraren)
        widget.search_bar.setText('Korsvägen')
        widget.toggle_pin()
        widget.search_bar.setText('Chalmers')
        widget.toggle_pin()

        restarted = VasttrafikDeparturesWidget(self.reseplaneraren)
        self.assertEqual(restarted.search_bar.text(), 'Korsvägen') # opens on the first pinned stop
        self.assertEqual(self.search(restarted, ''), ['Korsvägen'])

    def test_only_real_stops_can_be_pinned(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({'pinned_stops': ['Chalmers', 'Nedlagd hållplats']}, f)
        widget = VasttrafikDeparturesWidget(self.reseplaneraren)
        self.assertEqual(widget.config['pinned_stops'], ['Chalmers'])

        widget.search_bar.setText('Brunns')
        widget.toggle_pin()
        self.assertEqual(widget.config['pinned_stops'], ['Chalmers'])

if __name__ == '__main__':
    unittest.main()
