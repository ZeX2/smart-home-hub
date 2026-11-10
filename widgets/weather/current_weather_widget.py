try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from datetime import date

from api.smhi.smhi import sun_text
from api.pollen.pollen import LEVELS
from common.qthreading import Worker, get_thread_pool

class CurrentWeatherUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.setFixedSize(275, 190)
        self.setObjectName('CurrentWeather')
        self.setStyleSheet('QFrame#CurrentWeather {border: 0px solid black; border-radius: 25px}')

        column = QtWidgets.QVBoxLayout(self)
        self.layout = QtWidgets.QHBoxLayout()
        column.addLayout(self.layout)
        self.info_label = QtWidgets.QLabel()
        self.info_label.setStyleSheet('font-size: 15px')
        column.addWidget(self.info_label)

        self.temp_label = QtWidgets.QLabel('N/A')
        self.temp_label.setFont(QtGui.QFont('', 50))
        self.layout.addWidget(self.temp_label)

        self.spacer = QtWidgets.QSpacerItem(5, 50)
        self.layout.addSpacerItem(self.spacer)

        self.symb_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.symb_layout)

        self.weather_label = QtWidgets.QLabel('N/A')
        self.weather_label.setFont(QtGui.QFont('', 18))
        self.weather_label.setWordWrap(True)
        self.symb_layout.addWidget(self.weather_label)

        self.weather_symb = QtWidgets.QLabel()
        self.weather_symb.setFixedSize(int(260/2.8), int(180/2.8))
        self.weather_symb.setScaledContents(True)
        self.symb_layout.addWidget(self.weather_symb)

class CurrentWeatherWidget(CurrentWeatherUi):

    def __init__(self, smhi_forecast, pollen, lat, lon):
        super().__init__()
        self.setup_ui()

        self.smhi_forecast = smhi_forecast
        self.pollen = pollen
        self.top_pollen = ''
        self.lat = lat
        self.lon = lon
        self.thread_pool = get_thread_pool()

        self.update_weather()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_weather)
        self.timer.start(20*60*1000)

    def update_weather(self):
        self.worker = Worker(self.smhi_forecast.get_temperatures, self.lat, self.lon)
        self.worker.signals.result.connect(self.set_weather)
        self.thread_pool.start(self.worker)
        self.pollen_worker = Worker(self.pollen.get_pollen, self.lat, self.lon)
        self.pollen_worker.signals.result.connect(self.set_pollen)
        self.thread_pool.start(self.pollen_worker)
        self.update_info()

    def update_info(self):
        self.info_label.setText(sun_text(self.lat, self.lon, date.today()) + self.top_pollen)

    def set_pollen(self, result):
        levels = result[1]
        self.top_pollen = f'\nPollen: {levels[0][0]} {LEVELS[levels[0][1]].lower()}' if levels else ''
        self.update_info()

    def set_weather(self, forecast):
        weather_data = forecast[0]
        self.temp_label.setText(f'{round(weather_data[1])}°')
        wsymb_value = weather_data[2]
        self.weather_label.setText(self.smhi_forecast.get_wsymb2_meaning(wsymb_value))
        self.weather_symb.setPixmap(QtGui.QPixmap(self.smhi_forecast.get_wsymb2_path(wsymb_value)))
