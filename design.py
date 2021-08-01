from PySide2 import QtGui, QtCore, QtWidgets

from api.se_data.se_data import SEData
#https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# Jävligt nice widget?!

class WeatherWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.search_bar = QtWidgets.QLineEdit()
        self.layout.addWidget(self.search_bar)

        se_data = SEData()
        completer = QtWidgets.QCompleter(se_data.get_names())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search_bar.setCompleter(completer)

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

        self.page_one_layout = QtWidgets.QVBoxLayout()
        self.page_one_widget.setLayout(self.page_one_layout)

        self.page_one_layout.addWidget(QtWidgets.QLabel('PAGE ONE'))
        self.page_one_layout.addWidget(WeatherWidget())

        # Page 2
        self.page_two_widget = QtWidgets.QWidget()
        self.central_widget.insertTab(1, self.page_two_widget, 'Page Two')

        self.page_two_layout = QtWidgets.QVBoxLayout()
        self.page_two_widget.setLayout(self.page_two_layout)

        self.page_two_layout.addWidget(QtWidgets.QLabel('PAGE TWO'))
