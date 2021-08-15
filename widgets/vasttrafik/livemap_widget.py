import io
import re

import folium
from PySide2 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets

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
        if self.visibleRegion().isEmpty():
            return

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
        self.web_map.setHtml(map_data.getvalue().decode())
