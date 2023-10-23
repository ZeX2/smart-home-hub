import os

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.label_button import QLabelButton

NOTE_BOARD_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))

class NoteBoardUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.setFixedSize(275, 275)
        self.setObjectName('NoteBoard')
        self.setStyleSheet('QFrame#NoteBoard {border: 0px solid black; border-radius: 25px}')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.title_layout)

        self.title_label = QtWidgets.QLabel('Anslagstavla')
        self.title_label.setFont(QtGui.QFont('Lucida Console', 20))
        self.title_layout.addWidget(self.title_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, hData=QtWidgets.QSizePolicy.Expanding)
        self.title_layout.addSpacerItem(self.spacer)

        self.refresh_button = QLabelButton(os.path.join(NOTE_BOARD_WIDGET_DIR, 'refresh.png'))
        self.refresh_button.clicked.connect(self.update_note)
        self.refresh_button.setFixedSize(25, 25)
        self.title_layout.addWidget(self.refresh_button)

        self.note_label = QtWidgets.QLabel('N/A')
        self.note_label.setFont(QtGui.QFont('Lucida Console', 12))
        self.note_label.setWordWrap(True)
        self.layout.addWidget(self.note_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, vData=QtWidgets.QSizePolicy.Expanding)
        self.layout.addSpacerItem(self.spacer)

class NoteBoardWidget(NoteBoardUi):

    def __init__(self, notion_note):
        super().__init__()
        self.setup_ui()

        self.notion_note = notion_note

        self.update_note()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_note)
        self.timer.start(60*1000)

    def update_note(self):
        note_data = self.notion_note.get_note()
        self.note_label.setText(note_data)
