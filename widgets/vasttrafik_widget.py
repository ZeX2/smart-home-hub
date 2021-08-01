from PySide2 import QtGui, QtCore, QtWidgets

from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi

class VasttrafikUi(QtWidgets.QTabWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        self.search_bar = QtWidgets.QLineEdit()
        self.layout.addWidget(self.search_bar)
        self.search_bar.textChanged.connect(self.search_bar_updated)
        completer = QtWidgets.QCompleter(self.reseplaneraren.get_stop_names())
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setFilterMode(QtCore.Qt.MatchContains)
        self.search_bar.setCompleter(completer)

        self.departure_table = QtWidgets.QTreeWidget()
        self.departure_table.setHeaderHidden(True)
        self.departure_table.setColumnCount(2)
        self.departure_table.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.layout.addWidget(self.departure_table)

class VasttrafikWidget(VasttrafikUi):

    def __init__(self):
        super().__init__()
        self.reseplaneraren = VasttrafikReseplanerarenApi()
        self.setup_ui()
    
    def search_bar_updated(self):
        self.departure_table.clear()
        try:
            departure_data = self.reseplaneraren.get_departure_table(stop_name=self.search_bar.text())
        except IndexError:
            return

        print(departure_data)
