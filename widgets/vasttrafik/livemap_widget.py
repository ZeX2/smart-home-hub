import io
import re

import folium
from PySide2 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets, QtWebChannel

class Backend(QtCore.QObject):
    htmlChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(Backend, self).__init__(parent)
        self._html = ""

    @QtCore.Slot(str)
    def toHtml(self, html):
        self._html = html
        print(html)
        self.htmlChanged.emit()

    @property
    def html(self):
        return self._html

class WebEnginePage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, map_var, parent=None):
        super(WebEnginePage, self).__init__(parent)
        self.map_var = map_var
        self.loadFinished.connect(self.onLoadFinished)
        self._backend = Backend()
        self.backend.htmlChanged.connect(self.handle_htmlChanged)

    @property
    def backend(self):
        return self._backend

    @QtCore.Slot(bool)
    def onLoadFinished(self, ok):
        if ok:
            self.load_qwebchannel()
            self.load_object()

    def load_qwebchannel(self):
        file = QtCore.QFile(":/qtwebchannel/qwebchannel.js")
        if file.open(QtCore.QIODevice.ReadOnly):
            content = file.readAll()
            file.close()
            self.runJavaScript(content.data().decode())
        if self.webChannel() is None:
            channel = QtWebChannel.QWebChannel(self)
            self.setWebChannel(channel)

    def load_object(self):
        if self.webChannel() is not None:
            self.webChannel().registerObject(self.map_var, self.backend)
            script = fr"""
            new QWebChannel(qt.webChannelTransport, function (channel) {'{'}
                var backend = channel.objects.backend;
                var html = {self.map_var}.getZoom();
                backend.toHtml(html);
            {'}'});"""
            self.runJavaScript(script)

    def handle_htmlChanged(self):
        print(self.backend.html)

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

        self.update_web_map()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_web_map)
        self.timer.start(5000)

    def update_web_map(self):
        vehicles = self.reseplaneraren.get_live_map_vehicles(11760200, 12167400, 57605300, 57733500)
        map = folium.Map(title='LIVE MAP', location=[57.7143678, 11.9944993], zoom_start=15) #57.65, 11.9

        for vehicle in vehicles:
            name = vehicle["name"].replace('Bus ', '').replace('Spå ', '')
            icon_html = f'''<div style="border: 1px solid transparent; border-radius: 0.25rem;
                color: {vehicle["lcolor"]}; background-color: {vehicle["bcolor"]}; width: fit-content;
                height: fit-content; text-align: center; font-weight: bold;
                min-height: 2rem; min-width: 2rem;">{name}</div>'''
            icon = folium.DivIcon(icon_html)

            x = int(vehicle['x'])/1000000
            y = int(vehicle['y'])/1000000

            folium.Marker(location=[y, x], icon=icon).add_to(map)
        
        map_data = io.BytesIO()
        map.save(map_data, close_file=False)
        map_html = map_data.getvalue().decode()
        self.web_map.setHtml(map_html)
        #map_var = re.search(r'var\s(\S+)\s=\sL.map', map_html).group(1)
        #self.web_map.setPage(WebEnginePage(map_var))

        #channel = QWebChannel()
        #self.web_map.page().setWebChannel(channel)
        #channel.registerObject('{map_var}', self)

        #def test_func():
        #    print(self.web_map.page().runJavaScript(f'{map_var}.getZoom()', ))
        #self.web_map.loadFinished.connect(test_func)
