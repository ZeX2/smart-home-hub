try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common.qthreading import Worker, get_thread_pool
from common.fonts import app_font

class DailyWordUi(QtWidgets.QFrame):
    
    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.title_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.title_layout)

        self.title_label = QtWidgets.QLabel()
        self.title_label.setFont(app_font(16, True))
        self.title_label.setStyleSheet('color: gray')
        self.title_layout.addWidget(self.title_label)

        self.spacer = QtWidgets.QSpacerItem(5, 5, hData=QtWidgets.QSizePolicy.Expanding)
        self.title_layout.addSpacerItem(self.spacer)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(['ENG', 'SWE'])
        self.combo_box.currentTextChanged.connect(self.combo_box_changed)
        self.combo_box.setStyleSheet('''
            QComboBox {
                width: 30px;
                border: 1px solid gray;
                border-radius: 3px;
             }

             QComboBox::drop-down:button {
                border: 0px;
                width: 30px;
             }

             QComboBox::down-arrow {
                image: none;
             }
        ''')
        #print(self.combo_box.styleSheet())
        self.title_layout.addWidget(self.combo_box)

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setStyleSheet('background: transparent;')

        self.definition_label = QtWidgets.QLabel('N/A')
        self.definition_label.setFont(app_font(15))
        self.definition_label.setWordWrap(True)
        self.definition_label.setAlignment(QtCore.Qt.AlignTop)

        self.scroll_area.setWidget(self.definition_label)
        self.layout.addWidget(self.scroll_area)

class DailyWordWidget(DailyWordUi):

    def __init__(self, daily_word):
        super().__init__()
        self.setup_ui()

        self.daily_word = daily_word
        self.thread_pool = get_thread_pool()

        self.combo_box_changed(self.combo_box.currentText())

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.combo_box_changed(self.combo_box.currentText()))
        self.timer.start(60*60*1000)

    def combo_box_changed(self, value):
        get_word_and_def = self.daily_word.get_eng_word_and_def if value == 'ENG' else self.daily_word.get_swe_word_and_def
        self.worker = Worker(get_word_and_def)
        self.worker.signals.result.connect(lambda word_and_def: self.set_word(value, word_and_def))
        self.worker.signals.error.connect(lambda _: self.set_word(value, None))
        self.thread_pool.start(self.worker)

    def set_word(self, value, word_and_def):
        # The other language's answer can land after the user switched
        if value != self.combo_box.currentText():
            return
        if not word_and_def:
            self.definition_label.setText('Could not load the word of the day.')
            return

        self.title_label.setText('Word of the Day' if value == 'ENG' else 'Dagens Ord')
        word, definition = word_and_def
        self.definition_label.setText(f'{word}: {definition}')
