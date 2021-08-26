from PySide2 import QtGui, QtCore, QtWidgets

from widgets.clocks.analog_clock_widget import AnalogClockWidget
from widgets.clocks.digital_clock_widget import DigitalClockWidget
from widgets.weather.weather_widget import WeatherWidget
from widgets.weather.current_weather_widget import CurrentWeatherWidget
from widgets.vasttrafik.departures_widget import  VasttrafikDeparturesWidget
from widgets.vasttrafik.livemap_widget import VasttrafikLiveMapWidget
from widgets.spotify.spotify_widget import SpotifyWidget

# https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# Jävligt nice widget?!

class SmartHomeHubUi(QtWidgets.QMainWindow):

    def setup_ui(self):

        # Show fullscreen and background
        screen_size = QtWidgets.QApplication.primaryScreen().size()
        if (screen_size.width(), screen_size.height()) > (800, 480):
            self.setFixedSize(800, 480)
        else:
            self.showFullScreen()

        self.background_palette = QtGui.QPalette()
        self.background_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255,255,255))
        self.setPalette(self.background_palette)

        # Main widget and layout
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.setStyleSheet('''QTabWidget::tab-bar {alignment: left; margin: 2px; background: white; border: none;}
        QTabWidget::pane {border: none; background: white;}
        QTabBar::tab {border: none; padding: 10px; color: gray; background: white; font-size: 15px; font-family: "Lucida Console"; min-width: 100px; min-height: 20px; font-weight: 450}
        QTabBar::tab:selected {color: black;}
        ''')
        self.setCentralWidget(self.tab_widget)

        # Page 1
        self.page_one_widget = QtWidgets.QWidget()
        self.tab_widget.insertTab(0, self.page_one_widget, 'Hemma')

        self.page_one_layout = QtWidgets.QHBoxLayout()
        self.page_one_widget.setLayout(self.page_one_layout)

        self.page_one_layout.addWidget(CurrentWeatherWidget(self.smhi_forecast, 57.71667, 12))
        self.page_one_layout.addWidget(AnalogClockWidget())
        #self.page_one_layout.addWidget(WeatherWidget(self.se_data, self.smhi_forecast))

        # Page 2
        self.page_two_widget = QtWidgets.QWidget()
        self.tab_widget.insertTab(1, self.page_two_widget, 'Reseplaneraren')

        self.page_two_layout = QtWidgets.QVBoxLayout()
        self.page_two_widget.setLayout(self.page_two_layout)

        self.page_two_layout.addWidget(VasttrafikDeparturesWidget(self.reseplaneraren))

        # Page 3
        self.page_three_widget = QtWidgets.QWidget()
        self.tab_widget.insertTab(2, self.page_three_widget, 'Västtrafik Live Map')

        self.page_three_layout = QtWidgets.QVBoxLayout()
        self.page_three_widget.setLayout(self.page_three_layout)

        self.page_three_layout.addWidget(VasttrafikLiveMapWidget(self.reseplaneraren))

        # Page 4
        self.tab_widget.insertTab(3, SpotifyWidget(), 'Spotify')
