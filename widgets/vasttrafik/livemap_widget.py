import io
import os

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
        
        interceptor = Interceptor()
        self.web_map.page().profile().setUrlRequestInterceptor(interceptor)
        self.web_map.load(url)
        self.web_map.loadFinished.connect(self.get_and_update_web_map)

        self.since_last_clean_up = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.get_and_update_web_map)
        self.timer.start(5000)

    def get_web_map_data(self):
        return self.reseplaneraren.get_live_map_vehicles(11.760200, 12.167400, 57.605300, 57.733500)

    def update_web_map(self, vehicles):
        self.map_initialized = True
        if self.since_last_clean_up > 120:
            self.web_map.page().runJavaScript(f'''
                                              Object.values(layerGroups).forEach(layerGroup => {{layerGroup.clearLayers();}});
                                              for (var marker in markers) delete markers[marker];
                                              markers = {{}};         
            ''')
            self.since_last_clean_up = 0
        else:
            self.since_last_clean_up += 1

        for vehicle in vehicles:
            mode = vehicle['line']['transportMode']
            id = vehicle['detailsReference']
            name = vehicle['line']['name']#.replace('Bus', '').replace('Spå ', '').replace('Fär', '').strip()
            icon_html = f'''<div style="border: 1px solid transparent; border-radius: 0.25rem;
                color: {vehicle["line"]["foregroundColor"]}; background-color: {vehicle["line"]["backgroundColor"]}; width: fit-content;
                height: fit-content; text-align: center; font-weight: bold;
                min-height: 1rem; min-width: 1rem;">{name}</div>'''

            x = vehicle['longitude']
            y = vehicle['latitude']
            javascript = f'''if ('{id}' in markers) {{
                    markers['{id}'].setLatLng([{y}, {x}]).update()
                }} else {{
                    var icon_{id} = L.divIcon({{html: `{icon_html}` }});
                    markers['{id}'] = L.marker([{y}, {x}], {{icon: icon_{id} }}).addTo(layerGroups['{mode}']);
                }}'''
            
            self.web_map.page().runJavaScript(javascript)

    def get_and_update_web_map(self):
        if self.visibleRegion().isEmpty() and self.map_initialized:
            return
        
        self.worker = Worker(self.get_web_map_data)
        self.worker.signals.result.connect(self.update_web_map)
        self.thread_pool.start(self.worker)

    def tab_changed(self):
        self.get_and_update_web_map()
