import os

from PySide2 import QtGui, QtCore, QtWidgets

class QLabelButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        QtWidgets.QLabel.mousePressEvent(self, event)

class DailyWordUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.setFixedSize(300, 275)
        self.setObjectName('DailyWord')
        self.setStyleSheet('QFrame#DailyWord {border: 0px solid black; border-radius: 25px}')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.title_layout)

        self.title_label = QtWidgets.QLabel('N/A')
        self.title_label.setFont(QtGui.QFont('Lucida Console', 12))
        self.title_layout.addWidget(self.title_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, hData=QtWidgets.QSizePolicy.Expanding)
        self.title_layout.addSpacerItem(self.spacer)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(['ENG', 'SWE'])
        self.combo_box.currentTextChanged.connect(self.combo_box_changed)
        self.combo_box.setStyleSheet('''
            QComboBox {border: 0px}
            QComboxBox::down-arrow {border: 0px}
            QComboBox::drop-down {border: 0px}
        ''')
        self.title_layout.addWidget(self.combo_box)

        self.definition_label = QtWidgets.QLabel('N/A')
        self.definition_label.setFont(QtGui.QFont('Lucida Console', 9))
        self.definition_label.setWordWrap(True)
        self.layout.addWidget(self.definition_label)

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
        