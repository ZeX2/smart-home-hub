import traceback, sys

try:
    from PySide6 import QtGui, QtCore, QtWidgets# type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets# type: ignore

def get_thread_pool():
    for widget in QtWidgets.QApplication.instance().topLevelWidgets():
        if isinstance(widget, QtWidgets.QMainWindow):
            return widget.thread_pool
    return None

class WorkerSignals(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)

class Worker(QtCore.QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
