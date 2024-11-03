import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.timed_toggle_buttons import QTimedToggleButton

UNLOCK_GATE_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))

class UnlockGateWidget(QtWidgets.QWidget):

    def __init__(self, unlock_gate):
        super().__init__()
        
        self.unlock_gate = unlock_gate

        self.setStyleSheet(f'''
            UnlockGateWidget {{
                border-image: url("{os.path.join(UNLOCK_GATE_WIDGET_DIR, 'block.png')}");
            }}
        ''')
        self.setAttribute(QtCore.Qt.WA_StyledBackground)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        column_to_row_ratio = 11/6
        rows = 10
        columns = int(rows*column_to_row_ratio)
        for i in range(rows):
            for j in range(columns):
                label = QtWidgets.QLabel(f'', alignment=QtCore.Qt.AlignCenter)
                label.setStyleSheet('''
                    QLabel {
                        background: transparent;
                    }                
                ''')
                self.layout.addWidget(label, i, j)

        button = QTimedToggleButton(os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_closed.svg'), 
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_red.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_green.svg'),
                                    lambda : self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[0]))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 8, 13)

        button = QTimedToggleButton(os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_closed.svg'), 
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_red.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_green.svg'),
                                    lambda : self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[1]))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 8, 8)

        button = QTimedToggleButton(os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_closed.svg'), 
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_red.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_green.svg'),
                                    lambda : self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[2]))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 2, 12)

        button = QTimedToggleButton(os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_closed.svg'), 
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_red.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_green.svg'),
                                    lambda : self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[3]))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 4, 14)

        button = QTimedToggleButton(os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_closed.svg'), 
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_red.svg'),
                                    os.path.join(UNLOCK_GATE_WIDGET_DIR, 'door_open_green.svg'),
                                    lambda : self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[4]))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 3, 6)
