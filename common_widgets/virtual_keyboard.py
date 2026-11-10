try:
    from PySide6 import QtCore, QtGui, QtWidgets # type: ignore
except:
    from PySide2 import QtCore, QtGui, QtWidgets # type: ignore

# Rows of every page are 11 keys wide (⇧ and ⌫ count as two), so all keys get the same size
LETTERS = ['qwertyuiopå', 'asdfghjklöä', 'zxcvbnm']
SYMBOLS = ['1234567890+', '-/:;()&@"?!', '.,\'_%*#=€']

class VirtualKeyboard(QtWidgets.QFrame):
    '''On-screen keyboard for the touchscreen. attach() a QLineEdit and tapping it opens the keyboard.'''

    def __init__(self, parent):
        super().__init__(parent)
        self.target = None
        self.hide()
        self.setStyleSheet('''
            QFrame {
                background-color: rgba(128, 128, 128, 0.95);
            }
            QPushButton {
                background-color: white;
                border: none;
                border-radius: 5px;
                font-size: 22px;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: rgba(211, 211, 211, 0.85);
            }
        ''')
        self.shift = self.key('⇧', self.update_shift)
        self.shift.setCheckable(True)

        self.pages = QtWidgets.QStackedWidget()
        self.pages.addWidget(self.page(LETTERS, '123', self.shift))
        self.pages.addWidget(self.page(SYMBOLS, 'abc'))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.pages)

    def page(self, rows, switch_label, first_key=None):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for chars in rows:
            row = QtWidgets.QHBoxLayout()
            for char in chars:
                row.addWidget(self.key(char, self.type_key), 1)
            layout.addLayout(row)
        if first_key:
            row.insertWidget(0, first_key, 2)
        row.addWidget(self.key('⌫', lambda: self.send_key(QtCore.Qt.Key_Backspace)), 2)

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addWidget(self.key(switch_label, self.switch_page), 2)
        bottom_row.addWidget(self.key(' ', self.type_key), 5)
        bottom_row.addWidget(self.key('⏎', lambda: self.send_key(QtCore.Qt.Key_Return, '\r')), 2)
        bottom_row.addWidget(self.key('Klar', self.hide), 2)
        layout.addLayout(bottom_row)
        return page

    def key(self, text, slot):
        button = QtWidgets.QPushButton(text.replace('&', '&&')) # A single & marks a shortcut and is hidden
        button.setFocusPolicy(QtCore.Qt.NoFocus) # Keep the cursor in the search bar
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        button.clicked.connect(slot)
        return button

    def send_key(self, key, text=''):
        # Real key events, so any text widget handles them its own way (Enter fires returnPressed etc.)
        for event_type in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
            QtWidgets.QApplication.sendEvent(self.target, QtGui.QKeyEvent(event_type, key, QtCore.Qt.NoModifier, text))

    def type_key(self):
        self.send_key(0, self.sender().text().replace('&&', '&')) # Key code 0: plain text, no special key
        if self.shift.isChecked():
            self.shift.click() # One capital at a time, like a phone keyboard

    def update_shift(self):
        for button in self.findChildren(QtWidgets.QPushButton):
            if len(button.text()) == 1: # Character keys, upper() leaves digits and symbols alone
                button.setText(button.text().upper() if self.shift.isChecked() else button.text().lower())

    def switch_page(self):
        self.pages.setCurrentIndex(1 - self.pages.currentIndex())

    def attach(self, line_edit):
        line_edit.installEventFilter(self) # Only this widget, app-wide filters crash PySide with web views
        completer = line_edit.completer()
        if completer:
            popup = completer.popup()
            # A Popup grabs all touches, so every other key tap would only close the suggestions
            popup.setWindowFlags(QtCore.Qt.ToolTip)
            # Finger-sized rows, few enough to stay above the keyboard
            popup.setStyleSheet('QListView { font-size: 20px; } QListView::item { padding: 6px; }')
            completer.setMaxVisibleItems(5)
            completer.activated.connect(self.hide)

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.target = source
            self.show()
        return False
