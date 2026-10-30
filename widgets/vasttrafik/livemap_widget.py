import io
import os
import json

try:
    from PySide6 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets, QtWebEngineCore # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets, QtWebEngineCore # type: ignore

from common.qthreading import Worker, get_thread_pool

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
LIVEMAP_PATH = os.path.join(FILE_DIR, 'livemap.html')

class Interceptor(QtWebEngineCore.QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9,es;q=0.8,de;q=0.7")

class VasttrafikLiveMapUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.web_map = QtWebEngineWidgets.QWebEngineView()
        self.layout.addWidget(self.web_map)

class VasttrafikLiveMapWidget(VasttrafikLiveMapUi):

    def __init__(self, reseplaneraren):
        super().__init__()
        self.setup_ui()
        self.reseplaneraren = reseplaneraren
        self.thread_pool = get_thread_pool()
        self.map_initialized = False

        url = QtCore.QUrl.fromLocalFile(LIVEMAP_PATH)
        # Qt 6 blocks the remote map tiles for a page loaded from a local file unless this is on (Qt 5 on the Pi loads them anyway)
        settings = self.web_map.settings()
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        # Qt 6.12 turns off local file access when remote access is turned on, which blocks leaflet.js; turn it back on
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)

        interceptor = Interceptor()
        self.web_map.page().profile().setUrlRequestInterceptor(interceptor)
        self.web_map.load(url)
        self.web_map.loadFinished.connect(self.get_and_update_web_map)

        self.loading = False

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.get_and_update_web_map)
        self.timer.start(5000)

    def get_web_map_data(self):
        return self.reseplaneraren.get_live_map_vehicles(11.760200, 12.167400, 57.605300, 57.733500)

    def update_web_map(self, vehicles):
        self.map_initialized = True
        # One call with all vehicles; updateVehicles in livemap.html moves, adds and removes markers
        self.web_map.page().runJavaScript(f'updateVehicles({json.dumps(vehicles)})')

    def get_and_update_web_map(self):
        if self.visibleRegion().isEmpty() and self.map_initialized:
            return

        # Skip while the last request is still running, so slow answers don't pile up in the shared thread pool
        if self.loading:
            return

        self.loading = True
        self.worker = Worker(self.get_web_map_data)
        self.worker.signals.result.connect(self.update_web_map)
        self.worker.signals.finished.connect(lambda: setattr(self, 'loading', False))
        self.thread_pool.start(self.worker)

    def tab_changed(self):
        self.get_and_update_web_map()
