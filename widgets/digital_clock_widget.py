from PySide2 import QtGui, QtCore, QtWidgets

class DigitalClockUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        self.time_label = QtWidgets.QLabel()
        self.time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.time_label.setFont(QtGui.QFont('Arial', 120, QtGui.QFont.Bold))
        self.layout.addWidget(self.time_label)

        self.date_label = QtWidgets.QLabel()
        self.date_label.setAlignment(QtCore.Qt.AlignCenter)
        self.date_label.setFont(QtGui.QFont('Arial', 50, QtGui.QFont.Bold))
        self.layout.addWidget(self.date_label)

class DigitalClockWidget(DigitalClockUi):

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.last_updated_date = QtCore.QDate.currentDate()
        self.updateDate()
        self.updateTime()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateClock)
        self.timer.start(1000)

    def updateClock(self):
        if self.last_updated_date != QtCore.QDate.currentDate():
            self.updateDate()

        self.updateTime()

    def updateDate(self):
        current_date = QtCore.QDate.currentDate()
        date_string = current_date.toString('dddd dd MMMM')
        self.date_label.setText(date_string)

    def updateTime(self):
        current_time = QtCore.QTime.currentTime()
        time_string = current_time.toString('hh:mm:ss')
        self.time_label.setText(time_string)

