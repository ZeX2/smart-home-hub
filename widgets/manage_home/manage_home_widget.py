import os
import json

import dirigera
from dirigera.devices.light import _bound_to_kelvin  # the same Kelvin/mired fix set_color_temperature() checks against
from dirigera.devices.scene import SceneType

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.toggle_buttons import QGraphicsPixmapItemToggleButton
from common_widgets.buttons import QGraphicsPixmapItemButton
from common.qthreading import Worker, get_thread_pool
from common.art import art_folder
from .dirigera_secret import TOKEN, IP_ADDRESS

FLOOR_PLAN_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'art', 'floor_plan.svg')

CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

art = art_folder('manage_home')

# Device types drawn on the floor plan: (icon when off/closed, icon when on/open)
ICONS = {
    'light': ('lightbulb_off.svg', 'lightbulb_on.svg'),
    'outlet': ('outlet_off.svg', 'outlet_on.svg'),
    'openCloseSensor': ('door_closed.svg', 'door_open.svg'),
    'environmentSensor': ('air_sensor.svg', 'air_sensor.svg'),
}

LOW_BATTERY = 10
WARN_BATTERY = 20

# (hue, saturation) presets for colour bulbs
SWATCHES = [(0, 1), (30, 1), (55, 1), (120, 1), (180, 1), (240, 1), (285, 1), (330, 0.5)]

AIR_FIELDS = [('currentTemperature', '{:.1f}°'), ('currentRH', '{}%'), ('currentPM25', 'PM2.5 {}'),
              ('vocIndex', 'VOC {}'), ('currentCO2', 'CO2 {}')]

def device_state(device):
    # Same camelCase keys as the hub's events, so events can be merged straight in
    return {**device.attributes.model_dump(by_alias=True), 'isReachable': device.is_reachable}

def merge_event(states, data):
    """Merge an event's data into states. Returns the device id, or None if it isn't a known device."""
    id = data.get('id')
    if id not in states:
        return None
    states[id].update(data.get('attributes') or {})
    if 'isReachable' in data:
        states[id]['isReachable'] = data['isReachable']
    return id

def is_active(device_type, state):
    return bool(state.get('isOpen' if device_type == 'openCloseSensor' else 'isOn'))

def air_label(state):
    return '  '.join(fmt.format(state[key]) for key, fmt in AIR_FIELDS if state.get(key) is not None)

def batteries(states, names):
    """(name, percentage) for every battery device, emptiest first."""
    # Unnamed devices are halves of another device (the light sensor in a motion sensor) and repeat its battery
    return sorted(((names[id], state['batteryPercentage']) for id, state in states.items()
                   if names.get(id) and state.get('batteryPercentage') is not None), key=lambda b: (b[1], b[0]))

def battery_icon(levels):
    lowest = min((percentage for _, percentage in levels), default=100)
    if lowest <= LOW_BATTERY:
        return 'battery_low.svg'
    if lowest <= WARN_BATTERY:
        return 'battery_half.svg'
    return 'battery_ok.svg'

def dim(light, level, is_on):
    light.set_light_level(level)
    if not is_on:
        light.set_light(lamp_on=True)

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

class Popup(QtWidgets.QFrame):
    """Dims the page and shows a panel on top. Tapping outside the panel closes it."""

    def __init__(self, parent, title, close_button=True):
        super().__init__(parent)
        self.setObjectName('popup')
        self.setGeometry(parent.rect())
        self.setStyleSheet('''
            #popup { background-color: rgba(0, 0, 0, 0.4); }
            #panel { background-color: white; border-radius: 10px; }
            QSlider { min-height: 44px; }
            QSlider::groove:horizontal { height: 8px; background: lightgray; border-radius: 4px; }
            QSlider::handle:horizontal { width: 36px; margin: -14px 0; background: gray; border-radius: 18px; }
        ''')

        self.panel = QtWidgets.QFrame(self)
        self.panel.setObjectName('panel')
        self.panel.setMinimumWidth(380)
        self.content = QtWidgets.QVBoxLayout(self.panel)

        header = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel(title)
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        header.addWidget(title_label)
        header.addStretch()
        if close_button:
            button = QtWidgets.QPushButton('✕')
            button.setFixedSize(44, 44)
            button.clicked.connect(self.hide)
            header.addWidget(button)
        self.content.addLayout(header)

    def open(self, bottom_left=None):
        """Centre the panel, or put its bottom-left corner at bottom_left (a point in the page)."""
        self.panel.adjustSize()
        if bottom_left is None:
            self.panel.move((self.width() - self.panel.width()) // 2, (self.height() - self.panel.height()) // 2)
        else:
            self.panel.move(min(bottom_left.x(), self.width() - self.panel.width()),
                            max(0, bottom_left.y() - self.panel.height()))
        self.show()
        self.raise_()

    def mousePressEvent(self, event):
        if not self.panel.geometry().contains(event.pos()):
            self.hide()

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
                background-image: url("{FLOOR_PLAN_PATH}");
                background-repeat: no-repeat;
                background-position: center;
            }}
        ''')
        self.view.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.scene = QtWidgets.QGraphicsScene(0, 0, self.width(), self.height())
        self.view.setScene(self.scene)
        self.view.fitInView(self.scene.sceneRect())


        self.drag_button = QGraphicsPixmapItemToggleButton(
            art('click.svg'),
            art('drag.svg'),
            w=50,
            h=50,
            active=False
        )
        self.drag_button.set_short_click_function(self.drag_button_pressed)
        self.scene.addItem(self.drag_button)
        self.drag_button.setPos(self.scene.width()+10, self.scene.height()-55)

        self.refresh_button = QGraphicsPixmapItemButton(
            art('refresh.svg'),
            lambda: self.restart_hub(),
            lambda: None,
            50,
            50
        )
        self.scene.addItem(self.refresh_button)
        self.refresh_button.setPos(self.scene.width()+10, 0)

        self.scenes_button = QGraphicsPixmapItemButton(art('scenes.svg'), lambda: self.open_scenes_popup(), lambda: None, 50, 50)
        self.scene.addItem(self.scenes_button)
        self.scenes_button.setPos(self.scene.width()+10, 70)
        self.scenes_button.setVisible(False)

        self.battery_button = QGraphicsPixmapItemButton(art('battery_ok.svg'), lambda: self.open_battery_popup(), lambda: None, 50, 50)
        self.scene.addItem(self.battery_button)
        self.battery_button.setPos(-20, self.scene.height()-55)  # bottom left, clear of the collapsed side menu

class ManageHomeWidget(ManageHomeUi):
    def __init__(self):
        super().__init__()
        self.setup_ui()

        try:
            with open(CONFIG_PATH, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}
            self.save_config()

        self.thread_pool = get_thread_pool()
        self.status_online = False
        self.states = {}
        self.scenes = []
        self.popup = None
        self.initialize_hub()
        self.initialize_devices()

        QtWidgets.QApplication.instance().aboutToQuit.connect(self.stop_listener)

    def drag_button_pressed(self):
        for id, b in self.buttons.items():
            b.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, self.drag_button.is_active())
            b.childItems()[0].setVisible(self.drag_button.is_active())
            self.refresh_item(id)
            if not self.drag_button.is_active():
                self.config[id]['x'] = b.x()
                self.config[id]['y'] = b.y()

        if not self.drag_button.is_active():
            self.save_config()

    def on_message(self, message):
        data = json.loads(message).get('data')
        # Scene and hub events arrive here too; only device events carry a known device id
        if not isinstance(data, dict):
            return
        id = merge_event(self.states, data)
        if id is None:
            return
        if id in self.buttons:
            self.refresh_item(id)
        self.update_battery_button()

    def on_error(self, message):
        print(message)

    def device_type(self, id):
        return self.config[id].get('device_type', self.config[id]['type'])  # configs saved before device_type was stored

    def refresh_item(self, id):
        b, state = self.buttons[id], self.states.get(id, {})
        b.set_state(is_active(self.device_type(id), state))
        reachable = state.get('isReachable', True)
        b.setOpacity(1 if reachable else 0.35)
        b.setEnabled(reachable or self.drag_button.is_active())  # still movable in drag mode
        if id in self.air_labels:
            self.air_labels[id].setPlainText(air_label(state))

    def batteries(self):
        return batteries(self.states, {id: device['name'] for id, device in self.config.items()})

    def update_battery_button(self):
        self.battery_button.setPixmap(QtGui.QIcon(art(battery_icon(self.batteries()))).pixmap(50, 50))

    def save_config(self):
        # Write a temp file and swap it in, so a power cut mid-write can't leave a half config.json
        with open(CONFIG_PATH + '.tmp', 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=True))
        os.replace(CONFIG_PATH + '.tmp', CONFIG_PATH)

    def toggle_device(self, id):
        if self.config[id]['type'] == 'light':
            self.dh_devices[id].set_light(lamp_on=self.buttons[id].is_active())
        if self.config[id]['type'] == 'outlet':
            self.dh_devices[id].set_on(outlet_on=self.buttons[id].is_active())

    def send(self, fn, *args):
        # Every hub call is an HTTP request, so keep it off the UI thread
        self.thread_pool.start(Worker(fn, *args))

    def new_popup(self, title, close_button=True):
        if self.popup:
            self.popup.hide()  # deleteLater only takes effect on the next event-loop pass
            self.popup.deleteLater()
        self.popup = Popup(self, title, close_button)
        return self.popup

    def add_slider(self, popup, label, low, high, value, on_release):
        popup.content.addWidget(QtWidgets.QLabel(label))
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(low, high)
        slider.setValue(value)
        slider.setTracking(False)  # one hub call when the finger lifts, not one per step
        slider.valueChanged.connect(on_release)
        popup.content.addWidget(slider)
        return slider

    def open_lamp_popup(self, id):
        if self.drag_button.is_active():
            return  # a long press in drag mode is a move
        light, state = self.dh_devices[id], self.states[id]
        can_receive = light.capabilities.can_receive
        popup = self.new_popup(self.config[id]['name'])

        if 'lightLevel' in can_receive:
            self.add_slider(popup, 'Brightness', 1, 100, state.get('lightLevel') or 100,
                            lambda level: self.send(dim, light, level, state.get('isOn')))

        if 'colorTemperature' in can_receive and state.get('colorTemperatureMin') and state.get('colorTemperatureMax'):
            low, high = sorted(_bound_to_kelvin(state[key]) for key in ('colorTemperatureMin', 'colorTemperatureMax'))
            slider = self.add_slider(popup, 'Warmth', low, high, state.get('colorTemperature') or low,
                                     lambda kelvin: self.send(light.set_color_temperature, kelvin))
            slider.setInvertedAppearance(True)  # warm (low Kelvin) on the right, so right = warmer

        if 'colorHue' in can_receive and 'colorSaturation' in can_receive:
            row = QtWidgets.QHBoxLayout()
            for hue, saturation in SWATCHES:
                swatch = QtWidgets.QPushButton()
                swatch.setFixedSize(40, 40)
                color = QtGui.QColor.fromHsvF(hue / 360, saturation, 1).name()
                swatch.setStyleSheet(f'background-color: {color}; border: 1px solid gray; border-radius: 20px;')
                swatch.clicked.connect(lambda _=False, h=hue, s=saturation: self.send(light.set_light_color, h, s))
                row.addWidget(swatch)
            popup.content.addLayout(row)

        popup.open()

    def open_battery_popup(self):
        popup = self.new_popup('Batteries', close_button=False)
        levels = self.batteries()
        grid = QtWidgets.QGridLayout()
        for row, (name, percentage) in enumerate(levels):
            label = QtWidgets.QLabel(f'{percentage}%')
            if percentage <= WARN_BATTERY:
                label.setStyleSheet(f'color: {"#e00000" if percentage <= LOW_BATTERY else "#c08000"}; font-weight: bold;')
            grid.addWidget(QtWidgets.QLabel(name), row, 0)
            grid.addWidget(label, row, 1, QtCore.Qt.AlignRight)
        if not levels:
            grid.addWidget(QtWidgets.QLabel('No battery levels yet'), 0, 0)
        popup.content.addLayout(grid)
        button_top_left = self.view.mapFromScene(self.battery_button.sceneBoundingRect().topLeft())
        popup.open(self.view.mapTo(self, button_top_left) - QtCore.QPoint(0, 5))

    def open_scenes_popup(self):
        popup = self.new_popup('Scenes')
        inner = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(inner)
        for scene in self.scenes:
            button = QtWidgets.QPushButton(scene.info.name)
            button.setMinimumHeight(50)
            button.clicked.connect(lambda _=False, s=scene: (self.send(s.trigger), popup.hide()))
            column.addWidget(button)

        area = QtWidgets.QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QtWidgets.QFrame.NoFrame)
        area.setWidget(inner)
        area.setMinimumHeight(min(inner.sizeHint().height(), 320))
        area.setMaximumHeight(320)
        QtWidgets.QScroller.grabGesture(area.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)
        popup.content.addWidget(area)
        popup.open()

    def stop_listener(self):
        # QThread.quit() can't end the websocket loop, and a QThread still running when Python exits makes Qt abort
        if self.status_online:
            self.dh.stop_event_listener()
            self.dlistener.wait(2000)

    def restart_hub(self):
        self.stop_listener()
        self.initialize_hub()

    def initialize_hub(self):
        # Listing the devices takes seconds (10 s to time out when the hub is offline), so connect off the UI thread
        self.worker = Worker(self.connect_hub)
        self.worker.signals.result.connect(self.hub_connected)
        self.thread_pool.start(self.worker)

    def connect_hub(self):
        dh = dirigera.Hub(ip_address=IP_ADDRESS, token=TOKEN)
        devices = {device.id: device for device in dh.get_all_devices()}
        scenes = sorted((s for s in dh.get_scenes() if s.type == SceneType.USER_SCENE), key=lambda s: s.info.name)
        return dh, devices, scenes

    def hub_connected(self, result):
        # Two quick refreshes can both connect, so stop the first one's listener
        self.stop_listener()
        self.dh, self.dh_devices, self.scenes = result
        self.states = {id: device_state(device) for id, device in self.dh_devices.items()}
        self.dlistener = DirigeraListener(self.dh)
        self.dlistener.on_message.connect(self.on_message)
        self.dlistener.on_error.connect(self.on_error)
        self.dlistener.start()
        self.status_online = True

        if self.popup:
            self.popup.hide()  # it holds the old connection's devices
        self.scenes_button.setVisible(bool(self.scenes))

        # Swap the offline buttons drawn while connecting for live ones
        for b in self.buttons.values():
            self.scene.removeItem(b)
        self.initialize_devices()
        self.update_battery_button()

    def initialize_devices(self):
        self.buttons = {}
        self.air_labels = {}
        if self.status_online:
            for id, device in self.dh_devices.items():
                config = self.config.setdefault(id, {'x': 0, 'y': 0})
                config.update(type=device.type, device_type=device.device_type, name=device.attributes.custom_name)
                config.pop('active', None)  # on/off now comes from the hub, not the config

            self.save_config()

        for id, device in self.config.items():
            device_type = self.device_type(id)
            if device_type not in ICONS:
                continue

            off, on = ICONS[device_type]
            self.buttons[id] = QGraphicsPixmapItemToggleButton(art(off), art(on if self.status_online else off), w=50, h=50)
            if self.status_online and device_type in ('light', 'outlet'):
                self.buttons[id].set_short_click_function(self.toggle_device, id)
            else:
                self.buttons[id].set_short_click_function(self.refresh_item, id)  # undo the tap's pixmap flip
            if self.status_online and device_type == 'light':
                self.buttons[id].set_long_click_function(self.open_lamp_popup, id)

            self.scene.addItem(self.buttons[id])
            self.buttons[id].setPos(device['x'], device['y'])

            button_text = QtWidgets.QGraphicsTextItem(device['name'])
            button_text.setDefaultTextColor(QtCore.Qt.gray)
            self.scene.addItem(button_text)
            button_text.setParentItem(self.buttons[id])
            button_text.setPos(-button_text.boundingRect().width()/2+17.5, 45)
            button_text.setVisible(False)

            if device_type == 'environmentSensor':
                self.air_labels[id] = QtWidgets.QGraphicsTextItem()
                self.air_labels[id].setParentItem(self.buttons[id])
                self.air_labels[id].setPos(42, 12)

            self.refresh_item(id)
