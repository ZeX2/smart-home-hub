import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.timed_toggle_buttons import QTimedToggleButton
from common.art import art_folder

UNLOCK_GATE_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))
art = art_folder('unlock_gate')

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

        # (gate index, row, column) of each door on the block image
        for gate_index, row, column in [(0, 8, 13), (1, 8, 8), (2, 2, 12), (3, 4, 14), (4, 3, 6)]:
            button = QTimedToggleButton(art('door_closed.svg'),
                                        art('door_open.svg'),
                                        art('door_open_red.svg'),
                                        art('door_open_green.svg'),
                                        # i=gate_index fixes the index now, else every button would open the last gate
                                        lambda i=gate_index: self.unlock_gate.unlock_door(self.unlock_gate.get_gates()[i]))
            button.setFixedSize(self.width()/columns, self.height()/rows)
            self.layout.addWidget(button, row, column)
