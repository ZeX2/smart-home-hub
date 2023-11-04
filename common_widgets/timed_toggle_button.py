try:
    from PySide6 import QtGui, QtCore, QtWidgets, QtTest# type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets, QtTest# type: ignore

from common.qthreading import Worker, get_thread_pool

class QTimedToggleButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, path_inactive, path_active, path_active_sad, path_active_happy, func, active=False):
        super().__init__()
        self.setScaledContents(True)
        self.active = active
        self.pixmaps = [QtGui.QPixmap(path_inactive), QtGui.QPixmap(path_active)]
        self.pixmaps_mode = [QtGui.QPixmap(path_active_sad), QtGui.QPixmap(path_active_happy)]
        self.func = func
        self.update_pixmap()
        
        self.setStyleSheet('')
        
        self.thread_pool = get_thread_pool()

    def isActive(self):
        return self.active

    def update_pixmap(self):
        self.setPixmap(self.pixmaps[self.active])

    def toggle_pixmap(self):
        self.active = not self.active
        self.update_pixmap()

    def function_finished(self, func_return):
        self.setPixmap(self.pixmaps_mode[func_return])      
        QtTest.QTest.qWait(3000)
        self.toggle_pixmap()

    def mouseReleaseEvent(self, event):
        if self.active:
            return

        self.toggle_pixmap()

        worker = Worker(self.func)
        worker.signals.result.connect(self.function_finished)
        self.thread_pool.start(worker)

        super().mousePressEvent(event)
