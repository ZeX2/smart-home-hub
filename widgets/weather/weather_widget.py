from datetime import date

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from api.smhi.smhi import daily_forecast, sun_text
from api.pollen.pollen import LEVELS
from common.qthreading import Worker, get_thread_pool

HOME_NAME = 'Göteborg'
HOURS_SHOWN = 24
WEEKDAYS = ['Mån', 'Tis', 'Ons', 'Tor', 'Fre', 'Lör', 'Sön']

def symbol(smhi_forecast, value, width):
    label = QtWidgets.QLabel()
    label.setPixmap(QtGui.QPixmap(smhi_forecast.get_wsymb2_path(value)).scaledToWidth(width, QtCore.Qt.SmoothTransformation))
    label.setAlignment(QtCore.Qt.AlignCenter)
    return label

def rain_text(mm, unit=' mm'):
    return f'{mm:.1f}{unit}' if mm and mm >= 0.1 else ''

def scroll_area():
    area = QtWidgets.QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QtWidgets.QFrame.NoFrame)
    # Swiped, not dragged by a bar, which would also cover the last row
    area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    QtWidgets.QScroller.grabGesture(area.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)
    return area

class WeatherUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.setStyleSheet('QLabel { font-size: 16px; } QLineEdit { font-size: 20px; }')
        self.layout = QtWidgets.QVBoxLayout(self)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText('Sök ort')
        # The data is ordered biggest place first, so 'göte' suggests Göteborg before Götebo
        completer = QtWidgets.QCompleter(list(self.se_data.get_names().drop_duplicates()), self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        self.layout.addWidget(self.search_bar)

        self.sun_label = QtWidgets.QLabel()
        self.pollen_label = QtWidgets.QLabel()
        self.pollen_label.setWordWrap(True)
        info = QtWidgets.QHBoxLayout()
        info.addWidget(self.sun_label)
        info.addWidget(self.pollen_label, 1)
        self.layout.addLayout(info)

        self.hourly_area = scroll_area()
        self.hourly_area.setFixedHeight(0) # Sized to the hours once they load
        self.layout.addWidget(self.hourly_area)

        self.daily_area = scroll_area()
        self.layout.addWidget(self.daily_area, 1)

class WeatherWidget(WeatherUi):

    def __init__(self, se_data, smhi_forecast, pollen, lat, lon):
        super().__init__()
        self.se_data = se_data
        self.smhi_forecast = smhi_forecast
        self.pollen = pollen
        self.home = (HOME_NAME, lat, lon)
        self.place = self.home
        self.setup_ui()

        self.search_bar.completer().activated.connect(self.search)
        self.search_bar.returnPressed.connect(lambda: self.search(self.search_bar.text()))

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_weather)
        self.timer.start(20*60*1000)

    def tab_changed(self):
        # Another city is a one-off look, the page always opens on home
        self.place = self.home
        self.search_bar.setText(HOME_NAME)
        self.update_weather()

    def search(self, name):
        rows = self.se_data.get_name(name)
        if len(rows) == 0:
            return
        # Places sharing a name take the biggest, the data is ordered that way
        self.place = (name, rows['latitude'].values[0], rows['longitude'].values[0])
        self.update_weather()

    def update_weather(self):
        if not self.isVisible():
            return
        _, lat, lon = place = self.place
        self.sun_label.setText(sun_text(lat, lon, date.today()))
        self.pollen_label.setText('')
        # Kept on self so they live until they report back
        self.forecast_worker = self.run(self.smhi_forecast.get_forecast, place, self.set_forecast)
        self.pollen_worker = self.run(self.pollen.get_pollen, place, self.set_pollen)

    def run(self, fn, place, on_result):
        worker = Worker(lambda: (place, fn(place[1], place[2])))
        worker.signals.result.connect(on_result)
        get_thread_pool().start(worker)
        return worker

    def set_pollen(self, result):
        place, (region, levels) = result
        if place != self.place: # An older search finishing last must not overwrite a newer one
            return
        self.pollen_label.setText(f'Pollen ({region}): ' + ', '.join(f'{name} {LEVELS[level].lower()}' for name, level in levels) if levels else '')

    def set_forecast(self, result):
        place, forecast = result
        if place != self.place:
            return
        hourly = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(hourly)
        for time, temp, symb, rain in forecast[:HOURS_SHOWN]:
            column = QtWidgets.QVBoxLayout()
            column.addWidget(QtWidgets.QLabel(f'{time:%H}'), alignment=QtCore.Qt.AlignCenter)
            column.addWidget(symbol(self.smhi_forecast, symb, 50))
            column.addWidget(QtWidgets.QLabel(f'{round(temp)}°'), alignment=QtCore.Qt.AlignCenter)
            column.addWidget(QtWidgets.QLabel(rain_text(rain, unit='')), alignment=QtCore.Qt.AlignCenter)
            row.addLayout(column)
        self.hourly_area.setWidget(hourly)
        # Exactly as tall as its content, any spare height would let a swipe scroll it vertically
        self.hourly_area.setFixedHeight(hourly.sizeHint().height())

        daily = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(daily)
        today = date.today()
        for i, (day, low, high, symb, rain) in enumerate(daily_forecast(forecast)):
            name = 'Idag' if day == today else f'{WEEKDAYS[day.weekday()]} {day.day}/{day.month}'
            temps = f'{round(low)}° / {round(high)}°' if round(low) != round(high) else f'{round(high)}°'
            for column, widget in enumerate([QtWidgets.QLabel(name), symbol(self.smhi_forecast, symb, 45), QtWidgets.QLabel(temps), QtWidgets.QLabel(rain_text(rain))]):
                grid.addWidget(widget, i, column)
        self.daily_area.setWidget(daily)
