import os
import datetime
from glob import glob
from random import shuffle
from itertools import cycle

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

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
from widgets.manage_home.manage_home_widget import ManageHomeWidget
from widgets.unlock_gate.unlock_gate_widget import UnlockGateWidget

# https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# Jävligt nice widget?!

DESIGN_DIR = os.path.dirname(os.path.realpath(__file__))
SIDE_MENU_WIDTH = 40
SIDE_MENU_ICON_WIDTH = 30
SIDE_MENU_EXTENDED_WIDTH = 170

icon_path = lambda fn : os.path.join(DESIGN_DIR, 'icons', fn)

class Screensaver(QtWidgets.QSplashScreen):

    def __init__(self, main_parent):
        super().__init__()
        self.main_parent = main_parent

        self.installEventFilter(self)
        self.activity_events = self.main_parent.add_to_receive_activity_events(self)

        self.inactivity_timer = QtCore.QTimer()
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.setInterval(5000)
        self.inactivity_timer.timeout.connect(self.start_screensaver)

        self.screensaver_timer = QtCore.QTimer()
        self.screensaver_timer.setSingleShot(True)
        self.screensaver_timer.setInterval(5*60*1000)
        self.screensaver_timer.timeout.connect(self.change_screensaver)

        self.paths = glob(os.path.join(DESIGN_DIR, 'screensaver_pics', '*'))
        shuffle(self.paths)
        self.paths = cycle(self.paths)
        
        self.w = self.main_parent.frameGeometry().width()
        self.h = self.main_parent.frameGeometry().height()

    def change_screensaver(self):
        pixmap = QtGui.QPixmap(self.w, self.h)
        pixmap.fill(QtGui.QColor('black'))
        if not datetime.time(0, 0) <= datetime.datetime.now().time() <= datetime.time(7, 15):
            img_pixmap = QtGui.QPixmap(next(self.paths))
            img_pixmap = img_pixmap.scaled(self.w, self.h, QtCore.Qt.KeepAspectRatio)
            painter = QtGui.QPainter(pixmap)
            x = (self.w - img_pixmap.width()) // 2
            y = (self.h - img_pixmap.height()) // 2
            painter.drawPixmap(x, y, img_pixmap)
            painter.end()
        self.setPixmap(pixmap)

    def start_screensaver(self):
        self.change_screensaver()
        self.show()
        self.screensaver_timer.start()

    def eventFilter(self, source, event):
        if event.type() in self.activity_events:
            if self.isVisible():
                self.finish(self.main_parent)
            else:
                self.inactivity_timer.start()
                self.screensaver_timer.stop()
            return True

        return super().eventFilter(source, event)

class SideMenyButton(QtWidgets.QPushButton):
    top = 0

    def __init__(self, parent, text, icon_path, stacked_widget=None, widget=None, top=None):
        super().__init__()
        if top:
            self.top = top

        self.setParent(parent)
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.setGeometry(QtCore.QRect(0, self.top, SIDE_MENU_EXTENDED_WIDTH, SIDE_MENU_WIDTH))
        self.setMinimumSize(0, SIDE_MENU_WIDTH)
        self.setStyleSheet(F'''
            QPushButton {{
                background: transparent;
                border: none;
                text-align: left;
                padding-left: {int((SIDE_MENU_WIDTH-SIDE_MENU_ICON_WIDTH)/2)}px;
                padding-top: {int((SIDE_MENU_WIDTH-SIDE_MENU_ICON_WIDTH)/2)}px;
                padding-bottom: {int((SIDE_MENU_WIDTH-SIDE_MENU_ICON_WIDTH)/2)}px;
            }}
            QPushButton:pressed {{
                background-color: rgba(211, 211, 211, 0.85);
            }}
        ''')
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        icon = QtGui.QIcon()
        icon.addFile(icon_path, QtCore.QSize(), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(SIDE_MENU_ICON_WIDTH, SIDE_MENU_ICON_WIDTH))

        self.label = QtWidgets.QLabel(text)
        self.label.setStyleSheet(f'''
            QLabel {{
                background: transparent;
                padding-left: {SIDE_MENU_ICON_WIDTH}px;
            }}
        ''')
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.layout.addWidget(self.label)

        if stacked_widget and widget:
            stacked_widget.addWidget(widget)
            self.clicked.connect(lambda: stacked_widget.setCurrentWidget(widget))

        if isinstance(widget, Screensaver):
            self.clicked.connect(widget.start_screensaver)

        if not top:
            SideMenyButton.top += SIDE_MENU_WIDTH

class SmartHomeHubUi(QtWidgets.QMainWindow):

    def setup_ui(self):
        # Show fullscreen and background
        self.setWindowTitle('Smart Home Hub')
        screen_size = QtWidgets.QApplication.primaryScreen().size()
        self.setFixedSize(800, 480)
        if (screen_size.width(), screen_size.height()) < (1000, 500):
            self.showFullScreen()
            QtWidgets.QApplication.instance().setOverrideCursor(QtCore.Qt.BlankCursor)

        self.background_palette = QtGui.QPalette()
        self.background_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 255, 255))
        self.setPalette(self.background_palette)

        # Central widget and layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Side meny
        self.side_menu = QtWidgets.QFrame(self.central_widget)
        self.side_menu.setGeometry(QtCore.QRect(0, 0, SIDE_MENU_WIDTH, self.height()+5))
        self.side_menu.setStyleSheet('''
            QFrame {
                background-color: 	rgba(128, 128, 128, 0.95);
            }
        ''')
        self.side_menu.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.side_menu.setFrameShadow(QtWidgets.QFrame.Raised)

        # Main stacked widget
        self.stacked_widget = QtWidgets.QStackedWidget(self.central_widget)
        self.stacked_widget.setGeometry(QtCore.QRect(SIDE_MENU_WIDTH, 0, self.width()-SIDE_MENU_WIDTH, self.height()))

        # Home Widget
        self.home_widget = QtWidgets.QWidget()
        self.home_layout = QtWidgets.QGridLayout()
        self.home_layout.setContentsMargins(10, 10, 10, 10)
        self.home_widget.setLayout(self.home_layout)
        self.home_layout.setAlignment(QtCore.Qt.AlignAbsolute)
        self.home_layout.setSpacing(30)

        self.home_layout.addWidget(CurrentWeatherWidget(self.smhi_forecast, 57.71667, 12), 0, 0, QtCore.Qt.AlignCenter)
        self.home_layout.addWidget(AnalogClockWidget(), 0, 1, QtCore.Qt.AlignCenter)
        self.home_layout.addWidget(NoteBoardWidget(self.notion_note), 1, 0, QtCore.Qt.AlignCenter)
        self.home_layout.addWidget(DailyWordWidget(self.daily_word), 1, 1, QtCore.Qt.AlignCenter)
        #self.home_layout.addWidget(WeatherWidget(self.se_data, self.smhi_forecast))
        
        # Add side meny buttons
        self.side_menu_button = SideMenyButton(self.side_menu, 'Meny', os.path.join(DESIGN_DIR, 'icons', 'bars.svg'))
        self.side_menu_button.clicked.connect(self.side_menu_animate)
        SideMenyButton(self.side_menu, 'Hemma', icon_path('home.svg'), self.stacked_widget, self.home_widget)
        SideMenyButton(self.side_menu, 'Reseplaneraren', icon_path('tram.svg'), self.stacked_widget, VasttrafikDeparturesWidget(self.reseplaneraren))
        SideMenyButton(self.side_menu, 'Västtrafik Live Map', icon_path('map.svg'), self.stacked_widget, VasttrafikLiveMapWidget(self.reseplaneraren))
        SideMenyButton(self.side_menu, 'Spotify', icon_path('spotify.svg'), self.stacked_widget, SpotifyWidget())
        SideMenyButton(self.side_menu, 'Daily Painting', icon_path('paintbrush.svg'), self.stacked_widget, DailyPaintingWidget(self.daily_painting_data))
        SideMenyButton(self.side_menu, 'Manage Home', icon_path('lightbulb.svg'), self.stacked_widget, ManageHomeWidget())
        SideMenyButton(self.side_menu, 'Unlock Gates', icon_path('lock.svg'), self.stacked_widget, UnlockGateWidget(self.unlock_gate))
        SideMenyButton(self.side_menu, 'Screensaver', icon_path('gallery.svg'), widget=Screensaver(self), top=self.height()-SIDE_MENU_WIDTH*2)
        SideMenyButton(self.side_menu, 'Settings', icon_path('settings.svg'), top=self.height()-SIDE_MENU_WIDTH)

        self.stacked_widget.raise_()
        self.side_menu.raise_()
