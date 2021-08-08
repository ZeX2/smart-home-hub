from PySide2 import QtGui, QtCore, QtWidgets

from design import SmartHomeHubUi

from api.se_data.se_data import SEData
from api.smhi.smhi import SMHIForecastApi
from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi

class SmartHomeHub(SmartHomeHubUi):

    def __init__(self):
        super().__init__()

        # Initialize APIs
        self.se_data = SEData()
        self.reseplaneraren = VasttrafikReseplanerarenApi()
        self.smhi_forecast = SMHIForecastApi()

        self.setup_ui()
        self.show()
