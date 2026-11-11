import os
import json
from datetime import datetime, timezone

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common.qthreading import Worker, get_thread_pool
from common.art import art_folder

VASTTRAFIK_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(VASTTRAFIK_WIDGET_DIR, 'config.json')
art = art_folder('vasttrafik')

VECHILE_TYPE_SORT_ORDER = {'tram': 0, 'bus': 1} # Västtrafik sends transportMode in lowercase

def get_tram_sort_key(tram_data):
    return (
        VECHILE_TYPE_SORT_ORDER.get(tram_data['type'], 1000),
        len(tram_data['short_name']),
        tram_data['short_name']
    )

class LineIcon(QtWidgets.QLabel):

    def __init__(self, short_name, fg_color, bg_color):
        super().__init__(short_name)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(20, 20)
        self.setStyleSheet(f''' border: 2px solid transparent; border-radius: 5px; font-weight: bold;
            color: {fg_color}; background-color: {bg_color}; font-size: 17px; min-height: 20px; min-width: 20px;''')
        # margin-right: 0.3125rem; margin-bottom: 0.3125rem; padding: 1px 3px; 

class FingerSizedIconsStyle(QtWidgets.QProxyStyle):
    '''Qt draws icons inside a search bar at the small icon size, 16 px, a bit small to tap on the touchscreen.'''

    def pixelMetric(self, metric, option=None, widget=None):
        if metric == QtWidgets.QStyle.PM_SmallIconSize:
            return 20
        return super().pixelMetric(metric, option, widget)

class UnfilteredCompleter(QtWidgets.QCompleter):
    '''Shows its list as it is. The widget filters it, since Qt would drop the pinned stops that don't match.'''

    def splitPath(self, path):
        return [''] # Nothing to match, so every row shows

class VasttrafikDeparturesUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        pinned_stops = self.config['pinned_stops']
        self.search_bar = QtWidgets.QLineEdit(pinned_stops[0] if pinned_stops else 'Chalmers')
        self.search_bar_style = FingerSizedIconsStyle() # Kept here, setStyle doesn't take ownership
        self.search_bar.setStyle(self.search_bar_style)
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.get_and_update_departures_table)
        self.search_bar.textChanged.connect(self.update_pin_button)
        self.search_bar.textEdited.connect(self.update_search_results)
        self.stop_names_model = QtCore.QStringListModel()
        self.search_bar.setCompleter(UnfilteredCompleter(self.stop_names_model, self))

        pinned_list_action = self.search_bar.addAction(QtGui.QIcon(art('pinned_list.svg')), QtWidgets.QLineEdit.LeadingPosition)
        pinned_list_action.triggered.connect(self.show_pinned_stops)
        self.pin_action = self.search_bar.addAction(QtGui.QIcon(art('pin_off.svg')), QtWidgets.QLineEdit.TrailingPosition)
        self.pin_action.triggered.connect(self.toggle_pin)

        self.departure_table = QtWidgets.QTreeWidget()
        #self.departure_table.setContentsMargins(100, 100, 100, 100)
        self.departure_table.setHeaderHidden(True)
        self.departure_table.setColumnCount(3)
        self.departure_table.setColumnWidth(1, 350)
        #self.departure_table.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.layout.addWidget(self.departure_table)

class VasttrafikDeparturesWidget(VasttrafikDeparturesUi):

    def __init__(self, reseplaneraren):
        super().__init__()
        self.reseplaneraren = reseplaneraren
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except (FileNotFoundError, ValueError):
            self.config = {}
        stop_names = self.reseplaneraren.get_stop_names()
        # Stops Västtrafik has renamed or removed since they were pinned drop out
        self.config['pinned_stops'] = [stop for stop in self.config.get('pinned_stops', ['Chalmers']) if stop in stop_names]
        self.setup_ui()
        self.update_pins()
        self.thread_pool = get_thread_pool()
        self.table_initialized = False

        self.get_and_update_departures_table()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.get_and_update_departures_table)
        self.timer.start(20*1000)

    def get_arrival_times_label(self, times, rt_times):
        arrival_minutes = []
        for time, rt_time in zip(times, rt_times):
            if rt_time:
                arrival_minutes.append((round((rt_time - datetime.now(timezone.utc)).total_seconds()/60), False))
            else:
                arrival_minutes.append((round((time - datetime.now(timezone.utc)).total_seconds()/60), True))
        arrival_minutes = sorted(arrival_minutes, key=lambda x: x[0])
    
        if arrival_minutes[0][0] == 0:
            arrival_minutes[0] = ('nu', arrival_minutes[0][1])

        html_label = ['<style> td {padding: 0 5px} </style> <table> <tr>']
        for arrival in arrival_minutes:
            if arrival[1]:
                html_label.append(f'<td><p style="color:red; text-decoration: line-through;">{arrival[0]}</p></td>')
            elif arrival[0] == 'nu':
                html_label.append(f'<td><b>nu</b></td>')
            elif arrival[0] < 0:
                continue
            else:
                html_label.append(f'<td>{arrival[0]}</td>')
        html_label.append('</tr> </table>')

        arrival_label = QtWidgets.QLabel(' '.join(html_label))

        return arrival_label

    def get_departures_data(self):
        return self.reseplaneraren.get_departures_data_dict(stop_name=self.search_bar.text())

    def update_departures_table(self, departures_data):
        self.table_initialized = True

        self.departure_table.clear()
        for track, trams in sorted(departures_data.items(), key=lambda x: x[0]):
            track_item = QtWidgets.QTreeWidgetItem()
            self.departure_table.addTopLevelItem(track_item)
            self.departure_table.setItemWidget(track_item, 0, QtWidgets.QLabel(f'Läge {track}'))
            track_item.setExpanded(True)
            for i, (tram, tram_data) in enumerate(sorted(trams.items(), key=lambda x: get_tram_sort_key(x[1]))):
                tram_item = QtWidgets.QTreeWidgetItem()
                track_item.addChild(tram_item)
                self.departure_table.setItemWidget(tram_item, 0, LineIcon(tram_data['short_name'], tram_data['fg_color'], tram_data['bg_color']))
                self.departure_table.setItemWidget(tram_item, 1, QtWidgets.QLabel(f' {tram_data["direction"]}'))
                self.departure_table.setItemWidget(tram_item, 2, self.get_arrival_times_label(tram_data['time'], tram_data['rt_time']))

    def get_and_update_departures_table(self):
        if self.visibleRegion().isEmpty() and self.table_initialized:
            return

        if not self.search_bar.text() or self.search_bar.text() not in self.reseplaneraren.get_stop_names():
            return
        
        self.worker = Worker(self.get_departures_data)
        self.worker.signals.result.connect(self.update_departures_table)
        # Old minutes would be wrong, so show nothing rather than stale times
        self.worker.signals.error.connect(lambda _: self.departure_table.clear())
        self.thread_pool.start(self.worker)

    def tab_changed(self):
        self.get_and_update_departures_table()

    def toggle_pin(self):
        stop = self.search_bar.text()
        pinned_stops = self.config['pinned_stops']
        if stop in pinned_stops:
            pinned_stops.remove(stop)
        elif stop in self.reseplaneraren.get_stop_names():
            pinned_stops.append(stop)
        else:
            return
        self.save_config()
        self.search_bar.completer().popup().hide() # An open pinned list would otherwise fill up with every stop
        self.update_pins()

    def update_pins(self):
        self.other_stops = sorted(self.reseplaneraren.get_stop_names() - set(self.config['pinned_stops']))
        self.update_search_results(self.search_bar.text())
        self.update_pin_button()

    def update_search_results(self, text):
        # Pinned stops always lead, so an empty search lists only them
        text = text.casefold()
        matches = [stop for stop in self.other_stops if text in stop.casefold()] if text else []
        matches.sort(key=lambda stop: not stop.casefold().startswith(text)) # Names starting with the search first, each part still alphabetical
        self.stop_names_model.setStringList(self.config['pinned_stops'] + matches)

    def update_pin_button(self):
        icon = 'pin_on.svg' if self.search_bar.text() in self.config['pinned_stops'] else 'pin_off.svg'
        self.pin_action.setIcon(QtGui.QIcon(art(icon)))

    def show_pinned_stops(self):
        self.stop_names_model.setStringList(self.config['pinned_stops'])
        self.search_bar.completer().complete()

    def save_config(self):
        # Write a temp file and swap it in, so a power cut mid-write can't leave a half config.json
        with open(CONFIG_PATH + '.tmp', 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=True, ensure_ascii=False))
        os.replace(CONFIG_PATH + '.tmp', CONFIG_PATH)
