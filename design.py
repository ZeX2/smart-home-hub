try:
    from PySide6 import QtGui, QtCore, QtWidgets
except:
    from PySide2 import QtGui, QtCore, QtWidgets

from widgets.clocks.analog_clock_widget import AnalogClockWidget
from widgets.clocks.digital_clock_widget import DigitalClockWidget
from widgets.daily_word.daily_word_widget import DailyWordWidget
from widgets.weather.weather_widget import WeatherWidget
from widgets.weather.current_weather_widget import CurrentWeatherWidget
from widgets.vasttrafik.departures_widget import  VasttrafikDeparturesWidget
from widgets.vasttrafik.livemap_widget import VasttrafikLiveMapWidget
from widgets.spotify.spotify_widget import SpotifyWidget
from widgets.note_board.note_board_widget import NoteBoardWidget
from widgets.daily_painting.daily_painting_widget import DailyPaintingWidget

# https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# Jävligt nice widget?!

class SmartHomeHubUi(QtWidgets.QMainWindow):

    def setup_ui(self):

        # Show fullscreen and background
        self.setWindowTitle('Smart Home Hub')
        screen_size = QtWidgets.QApplication.primaryScreen().size()
        self.setFixedSize(800, 480)
        if (screen_size.width(), screen_size.height()) < (1000, 500):
            self.showFullScreen()

        self.background_palette = QtGui.QPalette()
        self.background_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255,255,255))
        self.setPalette(self.background_palette)

        # Main widget and layout
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.setStyleSheet('''
            QTabBar {font: 15px "Lucida Console"; font-weight: 450}
            QTabBar::tab {border: none; padding: 10px; color: gray; background: white}
            QTabBar::tab:selected {color: black;}
            QTabWidget::tab-bar {background: white;}
            QTabWidget::pane {border: none; background: white}
        ''')
        self.setCentralWidget(self.tab_widget)

        # Page 1
        self.page_one_widget = QtWidgets.QWidget()
        self.tab_widget.insertTab(0, self.page_one_widget, 'Hemma')

        self.page_one_layout = QtWidgets.QGridLayout()
        self.page_one_layout.setContentsMargins(15, 15, 15, 15)
        self.page_one_widget.setLayout(self.page_one_layout)
        self.page_one_layout.setAlignment(QtCore.Qt.AlignAbsolute)
        self.page_one_layout.setSpacing(60)

        self.page_one_layout.addWidget(CurrentWeatherWidget(self.smhi_forecast, 57.71667, 12), 0, 0, QtCore.Qt.AlignCenter)
        self.page_one_layout.addWidget(AnalogClockWidget(), 0, 1, QtCore.Qt.AlignCenter)
        self.page_one_layout.addWidget(NoteBoardWidget(self.notion_note), 1, 0, QtCore.Qt.AlignCenter)
        self.page_one_layout.addWidget(DailyWordWidget(self.daily_word), 1, 1, QtCore.Qt.AlignCenter)
        #self.page_one_layout.addWidget(WeatherWidget(self.se_data, self.smhi_forecast))

        # Page 2
        self.tab_widget.insertTab(1, VasttrafikDeparturesWidget(self.reseplaneraren), 'Reseplaneraren')

        # Page 3
        self.tab_widget.insertTab(2, VasttrafikLiveMapWidget(self.reseplaneraren), 'Västtrafik Live Map')

        # Page 4
        self.tab_widget.insertTab(3, SpotifyWidget(), 'Spotify')

        # Page 5
        self.tab_widget.insertTab(4, DailyPaintingWidget(self.daily_painting_data), 'Daily Painting')
