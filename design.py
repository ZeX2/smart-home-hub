
from PySide2 import QtGui, QtCore, QtWidgets

from widgets.clocks.analog_clock_widget import AnalogClockWidget
from widgets.clocks.digital_clock_widget import DigitalClockWidget
from widgets.weather.weather_widget import WeatherWidget
from widgets.vasttrafik.departures_widget import  VasttrafikDeparturesWidget
from widgets.vasttrafik.livemap_widget import VasttrafikLiveMapWidget

# https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# Jävligt nice widget?!

class SmartHomeHubUi(QtWidgets.QMainWindow):

    def setup_ui(self):

        # Show fullscreen and background
        self.showFullScreen()

        self.background_palette = QtGui.QPalette()
        self.background_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(100,0,0))
        self.setPalette(self.background_palette)

        # Main widget and layout
        self.central_widget = QtWidgets.QTabWidget(self)
        self.setStyleSheet('QTabWidget::tab-bar {alignment: center;}')
        self.setCentralWidget(self.central_widget)

        # Page 1
        self.page_one_widget = QtWidgets.QWidget()
        self.central_widget.insertTab(0, self.page_one_widget, 'Page One')

        self.page_one_layout = QtWidgets.QHBoxLayout()
        self.page_one_widget.setLayout(self.page_one_layout)

        self.page_one_layout.addWidget(AnalogClockWidget())
        self.page_one_layout.addWidget(WeatherWidget(self.se_data, self.smhi_forecast))

        # Page 2
        self.page_two_widget = QtWidgets.QWidget()
        self.central_widget.insertTab(1, self.page_two_widget, 'Page Two')

        self.page_two_layout = QtWidgets.QVBoxLayout()
        self.page_two_widget.setLayout(self.page_two_layout)

        self.page_two_layout.addWidget(QtWidgets.QLabel('PAGE TWO'))
        self.page_two_layout.addWidget(VasttrafikDeparturesWidget(self.reseplaneraren))
        self.page_two_layout.addWidget(VasttrafikLiveMapWidget(self.reseplaneraren))
