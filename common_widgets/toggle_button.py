try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

class QToggleButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, path_active, path_inactive, active=True):
        super().__init__()
        self.setScaledContents(True)
        self.active = active
        self.pixmaps = [QtGui.QPixmap(path_inactive), QtGui.QPixmap(path_active)]
        self.update_pixmap()
        
        self.setStyleSheet('')

    def isActive(self):
        return self.active

    def update_pixmap(self):
        self.setPixmap(self.pixmaps[self.active])

    def toggle_pixmap(self):
        self.active = not self.active
        self.update_pixmap()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        self.toggle_pixmap()
        super().mousePressEvent(event)
