try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from api.se_data.se_data import SEData
from api.smhi.smhi import SMHIForecastApi

# Current weather highlight!
# Two day weather widget
# 10 day weather widget
# Rain, clouds etc
# Sunrise, sunset

class WeatherUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        self.search_bar = QtWidgets.QLineEdit()
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.search_bar_updated)
        completer = QtWidgets.QCompleter(self.se_data.get_names())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search_bar.setCompleter(completer)

        self.two_day_weather_widget = QtWidgets.QTreeWidget()
        self.two_day_weather_widget.setHeaderHidden(True)
        self.two_day_weather_widget.setColumnCount(2)
        self.two_day_weather_widget.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.layout.addWidget(self.two_day_weather_widget)

class WeatherWidget(WeatherUi):

    def __init__(self, se_data, smhi_forecast):
        super().__init__()
        self.se_data = se_data
        self.smhi_forecast = smhi_forecast
        self.setup_ui()
    
    def search_bar_updated(self):
        self.two_day_weather_widget.clear()
        position_data = self.se_data.get_name(self.search_bar.text())
        if len(position_data) == 1:
            lat, lon = position_data['latitude'].values[0], position_data['longitude'].values[0]
            self.change_two_day_weather(lat, lon)

    def change_two_day_weather(self, lat, lon):
        weather_data = self.smhi_forecast.get_temperatures(lat, lon)

        for i, (time, temp) in enumerate(weather_data):
            self.two_day_weather_widget.insertTopLevelItem(i, QtWidgets.QTreeWidgetItem([str(time), str(temp)]))
