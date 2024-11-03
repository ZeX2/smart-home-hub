try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

class QToggleButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, path_inactive, path_active, active=False):
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

    def mousePressEvent(self, event):
        self.clicked.emit()
        self.toggle_pixmap()
        super().mousePressEvent(event)

class QGraphicsPixmapItemToggleButton(QtWidgets.QGraphicsPixmapItem):

    def __init__(self, path_inactive, path_active, short_click_func=lambda:None, long_click_func=lambda:None, w=None, h=None, active=False):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.long_click_func = long_click_func
        self.short_click_func = short_click_func
        self.active = active
        
        self.click_timer = QtCore.QElapsedTimer()
                
        if w and h:
            self.pixmaps = [QtGui.QIcon(path_inactive).pixmap(w, h),
                            QtGui.QIcon(path_active).pixmap(w, h)]
        else:
            self.pixmaps = [QtGui.QPixmap(path_inactive), QtGui.QPixmap(path_active)]

        self.update_pixmap()

    def isActive(self):
        return self.active

    def set_short_click_function(self, f):
        self.short_click_func = f

    def update_pixmap(self):
        self.setPixmap(self.pixmaps[self.active])

    def toggle_pixmap(self):
        self.active = not self.active
        self.update_pixmap()

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
        self.toggle_pixmap()
        self.short_click_func()

