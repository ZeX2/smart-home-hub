try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

class QLabelButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, path):
        super().__init__()
        self.setScaledContents(True)
        self.setPixmap(QtGui.QPixmap(path))

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)