from PySide2 import QtGui, QtCore, QtWidgets

from design import SmartHomeHubUi

class SmartHomeHub(SmartHomeHubUi):

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.show()
