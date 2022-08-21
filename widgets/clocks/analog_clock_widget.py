from PySide2 import QtGui, QtCore, QtWidgets

# Inspiration
# https://www.geeksforgeeks.org/create-analog-clock-using-pyqt5-in-python/
# https://github.com/baoboa/pyqt5/blob/master/examples/widgets/analogclock.py
# https://gitpress.io/u/1155/pyqt-example-analogclock
# https://www.pythonguis.com/tutorials/qml-animations-transformations/

class AnalogClockWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumSize(50, 50)
        self.setFixedSize(175, 175)

        self.hour_pointer = QtGui.QPolygon([QtCore.QPoint(3, 7),
                                        QtCore.QPoint(-3, 7),
                                        QtCore.QPoint(0, -60)])
        self.min_pointer = QtGui.QPolygon([QtCore.QPoint(3, 7),
                                        QtCore.QPoint(-3, 7),
                                        QtCore.QPoint(0, -80)])
        self.sec_pointer = QtGui.QPolygon([QtCore.QPoint(1, 1),
                                        QtCore.QPoint(-1, 1),
                                        QtCore.QPoint(0, -90)])

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        rec = min(self.width(), self.height())

        time = QtCore.QTime.currentTime()

        painter = QtGui.QPainter(self)

        def drawPointer(color, rotation, pointer):
            painter.setBrush(QtGui.QBrush(color))
            painter.save()
            painter.rotate(rotation)
            painter.drawConvexPolygon(pointer)
            painter.restore()

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(self.width()/2, self.height()/2)
        painter.scale(rec/200, rec/200)
        painter.setPen(QtCore.Qt.NoPen)

        drawPointer(QtCore.Qt.black, (30 * (time.hour() + time.minute() / 60)), self.hour_pointer)
        drawPointer(QtCore.Qt.black, (6 * (time.minute() + time.second() / 60)), self.min_pointer)
        drawPointer(QtCore.Qt.red, (6 * time.second()), self.sec_pointer)
  
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        for i in range(0, 60):
            if (i % 5) == 0:
                painter.drawLine(87, 0, 97, 0)
            painter.rotate(6)

        painter.end()
