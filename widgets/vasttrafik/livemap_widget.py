import io
import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets, QtWebEngineCore
except:
    from PySide2 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets, QtWebEngineCore

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

        url = QtCore.QUrl.fromLocalFile(LIVEMAP_PATH)
        
        interceptor = Interceptor()
        self.web_map.page().profile().setUrlRequestInterceptor(interceptor)
        self.web_map.load(url)

        self.update_web_map()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_web_map)
        self.timer.start(5000)

    def update_web_map(self):
        if self.visibleRegion().isEmpty():
                return

        vehicles = self.reseplaneraren.get_live_map_vehicles(11760200, 12167400, 57605300, 57733500)
        for vehicle in vehicles:
            id = vehicle['gid']
            name = vehicle['name'].replace('Bus', '').replace('Spå ', '').replace('Fär', '').strip()
            icon_html = f'''<div style="border: 1px solid transparent; border-radius: 0.25rem;
                color: {vehicle["lcolor"]}; background-color: {vehicle["bcolor"]}; width: fit-content;
                height: fit-content; text-align: center; font-weight: bold;
                min-height: 1rem; min-width: 1rem;">{name}</div>'''

            x = int(vehicle['x'])/1000000
            y = int(vehicle['y'])/1000000
            javascript = f'''if (typeof marker_{id} !== 'undefined') {{
                    marker_{id}.setLatLng([{y}, {x}]).update()
                }} else {{
                    var icon_{id} = L.divIcon({{html: `{icon_html}` }});
                    var marker_{id} = L.marker([{y}, {x}], {{icon: icon_{id} }}).addTo(map);
                }}'''
            
            self.web_map.page().runJavaScript(javascript)

    def tab_changed(self):
        self.update_web_map()
