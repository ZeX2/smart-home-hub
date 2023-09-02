import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.toggle_button import QToggleButton

MANAGE_HOME_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))

class ManageHomeWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet(f'''
            ManageHomeWidget {{
                background-image: url("{os.path.join(MANAGE_HOME_WIDGET_DIR, 'floor_plan.svg')}"); 
                background-repeat: no-repeat; 
                background-position: center;
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
                label = QtWidgets.QLabel('', alignment=QtCore.Qt.AlignCenter)
                label.setStyleSheet('''
                    QLabel {
                        background: transparent;
                    }                
                ''')
                self.layout.addWidget(label, i, j)

        button = QToggleButton(os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_on.svg'), os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_off.svg'))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 6, 12)
        
        button = QToggleButton(os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_on.svg'), os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_off.svg'))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 2, 12)

        button = QToggleButton(os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_on.svg'), os.path.join(MANAGE_HOME_WIDGET_DIR, 'lightbulb_off.svg'))
        button.setFixedSize(self.width()/columns, self.height()/rows)
        self.layout.addWidget(button, 4, 6)
