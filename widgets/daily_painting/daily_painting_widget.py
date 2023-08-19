import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets
except:
    from PySide2 import QtGui, QtCore, QtWidgets

FILE_DIR = os.path.dirname(os.path.realpath(__file__))

PAINTING_FMT = '''
            <p style="color: black; font-family: Verdana; font-size: 20px; text-align: left;">{title}<p>
            <p style="color: gray; font-family: Verdana; font-size: 15px; text-align: left;">{painter}<p>
            <p style="color: black; font-family: Verdana; font-size: 10px; text-align: left;">{description}<p>
'''

class DailyPaintingUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.painting_widget = None

class DailyPaintingWidget(DailyPaintingUi):

    def __init__(self, daily_painting_data):
        super().__init__()
        self.setup_ui()

        self.daily_painting_data = daily_painting_data

        self.update_random_painting()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_random_painting)
        self.timer.start(24*60*60*1000)

    def update_random_painting(self):
        self.daily_painting_data.random_painting()
        title, painter, description, path = self.daily_painting_data.get_painting()
        if not description:
            description = ''

        pixmap = QtGui.QPixmap(path)
        long = False
        if pixmap.width() > pixmap.height()*1.75:
            pixmap = pixmap.scaledToWidth(480)
        else:
            long = True
            pixmap = pixmap.scaledToHeight(350)

        if self.painting_widget:
            self.layout.removeWidget(self.painting_widget)
            self.painting_widget.deleteLater()

        self.painting_widget = QtWidgets.QWidget()
        self.layout.addWidget(self.painting_widget, alignment=QtCore.Qt.AlignCenter)
        self.painting_layout = QtWidgets.QHBoxLayout() if long else QtWidgets.QVBoxLayout()
        self.painting_widget.setLayout(self.painting_layout)

        self.spacer = QtWidgets.QSpacerItem(40, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.painting_layout.addSpacerItem(self.spacer)

        self.painting = QtWidgets.QLabel()
        self.painting.setPixmap(pixmap)
        self.painting_layout.addWidget(self.painting, alignment=QtCore.Qt.AlignCenter)

        self.spacer = QtWidgets.QSpacerItem(60, 60, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.painting_layout.addSpacerItem(self.spacer)

        self.painting_info = QtWidgets.QLabel()
        self.painting_info.setWordWrap(True)
        self.painting_info.setText(PAINTING_FMT.format(title=title, painter=painter, description=description))
        self.painting_layout.addWidget(self.painting_info)

        self.spacer = QtWidgets.QSpacerItem(40, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.painting_layout.addSpacerItem(self.spacer)
