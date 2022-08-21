import os

from PySide2 import QtGui, QtCore, QtWidgets

NOTE_BOARD_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))

class QLabelButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        QtWidgets.QLabel.mousePressEvent(self, event)

class NoteBoardUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.setFixedSize(275, 275)
        self.setObjectName('NoteBoard')
        self.setStyleSheet('QFrame#NoteBoard {border: 0px solid black; border-radius: 25px}')

        self.layout = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.title_layout)

        self.title_label = QtWidgets.QLabel('Anslagstavla')
        self.title_label.setFont(QtGui.QFont('Lucida Console', 12))
        self.title_layout.addWidget(self.title_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, hData=QtWidgets.QSizePolicy.Expanding)
        self.title_layout.addSpacerItem(self.spacer)

        self.refresh_button = QLabelButton()
        self.refresh_button.clicked.connect(self.update_note)
        self.refresh_button.setFixedSize(25, 25)
        self.refresh_button.setScaledContents(True)
        self.refresh_button.setPixmap(QtGui.QPixmap(os.path.join(NOTE_BOARD_WIDGET_DIR, 'refresh.png')))
        self.title_layout.addWidget(self.refresh_button)

        self.note_label = QtWidgets.QLabel('N/A')
        self.note_label.setFont(QtGui.QFont('Lucida Console', 10))
        self.note_label.setWordWrap(True)
        self.layout.addWidget(self.note_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, vData=QtWidgets.QSizePolicy.Expanding)
        self.layout.addSpacerItem(self.spacer)

class NoteBoardWidget(NoteBoardUi):

    def __init__(self, simplenote):
        super().__init__()
        self.setup_ui()

        self.simplenote = simplenote

        self.update_note()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_note)
        self.timer.start(60*1000)

    def update_note(self):
        note_data = self.simplenote.get_note()
        self.note_label.setText(note_data)
