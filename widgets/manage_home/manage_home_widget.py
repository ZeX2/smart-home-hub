import os
import json
import __main__

import dirigera

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.toggle_buttons import QGraphicsPixmapItemToggleButton
from common_widgets.buttons import QGraphicsPixmapItemButton
from .dirigera_secret import TOKEN, IP_ADDRESS

MAIN_ART_DIR = os.path.join(os.path.dirname(os.path.realpath(__main__.__file__)), 'common_art')
MANAGE_HOME_ART_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'art')

CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

LIGHT_OFF_PATH = os.path.join(MANAGE_HOME_ART_DIR, 'lightbulb_off.svg')
LIGHT_ON_PATH = os.path.join(MANAGE_HOME_ART_DIR, 'lightbulb_on.svg')
    
class ManageHomeUi(QtWidgets.QWidget):
    
    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.view = QtWidgets.QGraphicsView()
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.LosslessImageRendering)
        self.layout.addWidget(self.view)

        self.setStyleSheet(f'''
            QGraphicsView {{
                background-image: url("{os.path.join(MANAGE_HOME_ART_DIR, 'floor_plan.svg')}"); 
                background-repeat: no-repeat; 
                background-position: center;
            }}
        ''')
        self.view.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.scene = QtWidgets.QGraphicsScene(0, 0, self.width(), self.height())
        self.view.setScene(self.scene)
        self.view.fitInView(self.scene.sceneRect())


        self.drag_button = QGraphicsPixmapItemToggleButton(
            os.path.join(MANAGE_HOME_ART_DIR, 'click.svg'),
            os.path.join(MANAGE_HOME_ART_DIR, 'drag.svg'),
            w=50,
            h=50,
            active=False
        )
        self.drag_button.set_short_click_function(self.drag_button_pressed)
        self.scene.addItem(self.drag_button)
        self.drag_button.setPos(self.scene.width()+10, self.scene.height()-55)

        self.refresh_button = QGraphicsPixmapItemButton(
            os.path.join(MAIN_ART_DIR, 'refresh.svg'),
            lambda: print('hej2'),
            lambda: print('hej2long'),
            50,
            50
        )
        self.scene.addItem(self.refresh_button)
        self.refresh_button.setPos(self.scene.width()+10, 0)

class ManageHomeWidget(ManageHomeUi):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        try:
            with open(CONFIG_PATH, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {}
            self.save_config()

        self.buttons = {}
        self.dh = dirigera.Hub(ip_address=IP_ADDRESS, token=TOKEN)
        #self.dh.create_event_listener(on_message=self.on_message, on_error=self.on_error)
        self.initialize_devices()

    def drag_button_pressed(self):
        for id, b in self.buttons.items():
            b.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, self.drag_button.isActive())
            if not self.drag_button.isActive():
                self.config[id]['x'] = b.x()
                self.config[id]['y'] = b.y()

        if not self.drag_button.isActive():
            self.save_config()

    def on_message(self, ws, message: str):
        message_dict = json.loads(message)
        data = message_dict["data"]
        print(message_dict)
        print(data)
        print(ws)

    def on_error(self, ws, message: str):
        print(ws)
        print(message)

    def save_config(self):
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=True))

    def initialize_devices(self):
        self.dh_devices = self.dh.get_all_devices()
        
        for device in self.dh_devices:
            if device.id not in self.config:
                self.config[device.id] = {'x': 0, 'y': 0}

            if device.type == 'light':
                device.reload()
                button = QGraphicsPixmapItemToggleButton(LIGHT_OFF_PATH, LIGHT_ON_PATH, w=50, h=50, active=device.attributes.is_on)
                f = lambda : device.set_light(lamp_on=button.isActive())
                button.set_short_click_function(f)
                self.scene.addItem(button)
                button.setPos(self.config[device.id]['x'], self.config[device.id]['y'])
                self.buttons[device.id] = button
        
        self.save_config()
