from PySide2 import QtGui, QtCore, QtWidgets

from design import SmartHomeHubUi

from api.se_data.se_data import SEData
from api.smhi.smhi import SMHIForecastApi
from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi
from api.notion_note.notion_note import NotionNoteApi
from api.daily_word.daily_word import DailyWordApi

# Virtual keyboard inspo: https://github.com/sanjivktr/PyQt5-Virtual-Keyboard/blob/master/virtual_keyboard_controller.py
# https://github.com/githubuser0xFFFF/QtFreeVirtualKeyboard
# https://stackoverflow.com/questions/3103178/how-to-get-the-system-info-with-python
# https://www.geeksforgeeks.org/how-to-get-current-cpu-and-ram-usage-in-python/
# https://www.geeksforgeeks.org/get-your-system-information-using-python-script/
# 
class SmartHomeHub(SmartHomeHubUi):

    def __init__(self):
        super().__init__()

        # Initialize APIs
        self.se_data = SEData()
        self.reseplaneraren = VasttrafikReseplanerarenApi()
        self.smhi_forecast = SMHIForecastApi()
        self.notion_note = NotionNoteApi()
        self.daily_word = DailyWordApi()

        self.setup_ui()
        self.show()

    def tab_changed(self, index):
        pass #print(self.tab_widget.currentWidget())
