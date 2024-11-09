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

DEVICES_TO_BE_SHOWN = ['light', 'outlet']

class DirigeraListener(QtCore.QThread):
    on_message = QtCore.Signal(object)
    on_error = QtCore.Signal(object)

    def __init__(self, dh):
        super().__init__()
        self.dh = dh

    def run(self):
        self.dh.create_event_listener(on_message=self.on_message_, on_error=self.on_error_)

    def on_message_(self, ws, message):
        self.on_message.emit(message)
    
    def on_error_(self, ws, message):
        self.on_error.emit(message)

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

        self.status_online = False
        self.initialize_hub()
        self.initialize_devices()

    def drag_button_pressed(self):
        for id, b in self.buttons.items():
            b.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, self.drag_button.is_active())
            b.childItems()[0].setVisible(self.drag_button.is_active())
            if not self.drag_button.is_active():
                self.config[id]['x'] = b.x()
                self.config[id]['y'] = b.y()

        if not self.drag_button.is_active():
            self.save_config()

    def on_message(self, message):
        message_dict = json.loads(message)
        data = message_dict['data']
        if 'isOn' in data['attributes'] and data['type'] in DEVICES_TO_BE_SHOWN:
            self.toggle_button_state(data['id'], data['attributes']['isOn'])

    def on_error(self, message):
        print(message)

    def toggle_button_state(self, id, state):
        self.buttons[id].set_state(state)

    def save_config(self):
        with open(CONFIG_PATH, 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=True))

    def toggle_device(self, id):
        if self.config[id]['type'] == 'light':
            self.dh_devices[id].set_light(lamp_on=self.buttons[id].is_active())
        if self.config[id]['type'] == 'outlet':
            self.dh_devices[id].set_on(outlet_on=self.buttons[id].is_active())

    def initialize_hub(self):
        try:
            self.dh = dirigera.Hub(ip_address=IP_ADDRESS, token=TOKEN)
            self.dh_devices = {device.id: device for device in self.dh.get_all_devices()}
            self.dlistener = DirigeraListener(self.dh)
            self.dlistener.on_message.connect(self.on_message)
            self.dlistener.on_error.connect(self.on_error)
            self.dlistener.start()
            self.status_online = True
        except Exception as e:
            print(e)

    def initialize_devices(self):
        self.buttons = {}
        self.light_functions = {}
        if self.status_online:            
            for id, device in self.dh_devices.items():
                if id not in self.config:
                    self.config[id] = {'x': 0, 'y': 0}
                self.config[id]['type'] = device.type
                self.config[id]['name'] = device.attributes.custom_name
                if device.type in DEVICES_TO_BE_SHOWN:
                    self.config[id]['active'] = device.attributes.is_on

            self.save_config()

        for id, device in self.config.items():
            if self.config[id]['type'] in DEVICES_TO_BE_SHOWN:
                if self.status_online:
                    self.buttons[id] = QGraphicsPixmapItemToggleButton(LIGHT_OFF_PATH, LIGHT_ON_PATH, w=50, h=50, active=device['active'])
                    self.buttons[id].set_short_click_function(self.toggle_device, id)
                else:
                    self.buttons[id] = QGraphicsPixmapItemToggleButton(LIGHT_OFF_PATH, LIGHT_OFF_PATH, w=50, h=50)

                self.scene.addItem(self.buttons[id])
                self.buttons[id].setPos(device['x'], device['y'])

                button_text = QtWidgets.QGraphicsTextItem(device['name'])
                button_text.setDefaultTextColor(QtCore.Qt.gray)
                self.scene.addItem(button_text)
                button_text.setParentItem(self.buttons[id])
                button_text.setPos(-button_text.boundingRect().width()/2+17.5, 45)
                button_text.setVisible(False)
