import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

import resources

DAILY_WORD_DIR = os.path.dirname(os.path.realpath(__file__))
DROP_DOWN_ARROW_PATH = os.path.join(DAILY_WORD_DIR, 'refresh.png')

class DailyWordUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.setFixedSize(300, 250)
        self.setObjectName('DailyWord')
        self.setStyleSheet('QFrame#DailyWord {border: 0px solid black; border-radius: 25px}')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.title_layout)

        self.title_label = QtWidgets.QLabel()
        self.title_label.setFont(QtGui.QFont('Lucida Console', 18))
        self.title_layout.addWidget(self.title_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, hData=QtWidgets.QSizePolicy.Expanding)
        self.title_layout.addSpacerItem(self.spacer)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(['ENG', 'SWE'])
        self.combo_box.currentTextChanged.connect(self.combo_box_changed)
        self.combo_box.setStyleSheet(f'''
            QComboBox {{
                width: 30px;
                image: url(:/drop_down_arrow.png);
                border: 1px solid gray;
                border-radius: 3px;
             }}
 
             QComboBox::drop-down:button {{
                image: url(:/drop_down_arrow.png);
                border: 0px;
                width: 30px;
             }}
 
             QComboBox::down-arrow {{
                image: url(:/drop_down_arrow.png);
             }}
        ''')
        #print(self.combo_box.styleSheet())
        self.title_layout.addWidget(self.combo_box)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setBackgroundRole(QtGui.QPalette.Light)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setStyleSheet('background-color: none;')

        self.definition_label = QtWidgets.QLabel('N/A')
        self.definition_label.setFont(QtGui.QFont('Lucida Console', 12))
        self.definition_label.setWordWrap(True)

        self.scroll_area.setWidget(self.definition_label)
        self.layout.addWidget(self.scroll_area)

        self.spacer = QtWidgets.QSpacerItem(5, 5, vData=QtWidgets.QSizePolicy.Expanding)
        self.layout.addSpacerItem(self.spacer)

class DailyWordWidget(DailyWordUi):

    def __init__(self, daily_word):
        super().__init__()
        self.setup_ui()

        self.daily_word = daily_word

        self.combo_box_changed(self.combo_box.currentText())

    def combo_box_changed(self, value):
        if value == 'ENG':
            word, definition = self.daily_word.get_eng_word_and_def()
            self.title_label.setText('Word of the Day')
        elif value == 'SWE':
            word, definition = self.daily_word.get_swe_word_and_def()
            self.title_label.setText('Dagens Ord')
        self.definition_label.setText(f'{word}: {definition}')
        