from datetime import datetime

try:
    from PySide6 import QtGui, QtCore, QtWidgets
except:
    from PySide2 import QtGui, QtCore, QtWidgets

VECHILE_TYPE_SORT_ORDER = {'TRAM': 0, 'BUS': 1}

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

class VasttrafikDeparturesUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        self.search_bar = QtWidgets.QLineEdit('Olskrokstorget')
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.get_and_update_departure_table)
        completer = QtWidgets.QCompleter(self.reseplaneraren.get_stop_names())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search_bar.setCompleter(completer)

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
        self.setup_ui()

        self.table_initialized = False

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_departure_table)
        self.get_and_update_departure_table()

    def get_arrival_times_label(self, times, rt_times):
        arrival_minutes = []
        for time, rt_time in zip(times, rt_times):
            if rt_time:
                arrival_minutes.append((round((rt_time - datetime.now()).total_seconds()/60), False))
            else:
                arrival_minutes.append((round((time - datetime.now()).total_seconds()/60), True))
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

    def update_departure_table(self):
        if self.visibleRegion().isEmpty() and self.table_initialized:
                return

        self.table_initialized = True
        departure_data = self.reseplaneraren.get_departure_table(stop_name=self.search_bar.text())

        self.departure_table.clear()
        for track, trams in sorted(departure_data.items(), key=lambda x: x[0]):
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

    def get_and_update_departure_table(self):
        if not self.search_bar.text() or self.search_bar.text() not in self.reseplaneraren.get_stop_names():
            self.timer.stop()
            return

        self.update_departure_table()
        self.timer.start(20*1000)

    def tab_changed(self):
        self.get_and_update_departure_table()
