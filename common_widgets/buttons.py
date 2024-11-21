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

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class QGraphicsPixmapItemButton(QtWidgets.QGraphicsPixmapItem):

    def __init__(self, path, short_click_func, long_click_func=lambda:None, w=None, h=None):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)

        self.long_click_func = long_click_func
        self.short_click_func = short_click_func
        self.click_timer = QtCore.QElapsedTimer()

        if w and h:
            self.setPixmap(QtGui.QIcon(path).pixmap(w, h))
        else:
            self.setPixmap(QtGui.QPixmap(path))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setSelected(False)
        self.click_timer.start()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setSelected(False)
        if self.click_timer.elapsed() < 200:
            self.short_click()
        else:
            self.long_click()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.setSelected(False)

    def long_click(self):
        self.long_click_func()

    def short_click(self):
        self.short_click_func()
