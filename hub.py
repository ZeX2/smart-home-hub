try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from design import SmartHomeHubUi, SIDE_MENU_WIDTH, SIDE_MENU_EXTENDED_WIDTH

from api.se_data.se_data import SEData
from api.smhi.smhi import SMHIForecastApi
from api.vasttrafik.vasttrafik import VasttrafikReseplanerarenApi
from api.notion_note.notion_note import NotionNoteApi
from api.daily_word.daily_word import DailyWordApi
from api.daily_painting.daily_painting_data import DailyPaintingData
from api.unlock_gate.unlock_gate import UnlockGateApi

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
        self.daily_painting_data = DailyPaintingData()
        self.unlock_gate = UnlockGateApi()

        # Thread pool
        self.thread_pool = QtCore.QThreadPool()

        self.setup_ui()
        self.show()

    def tab_changed(self, index):
        widget = self.stacked_widget.currentWidget()
        tab_changed = getattr(widget, 'tab_changed', None)
        if callable(tab_changed):
            tab_changed()

    def side_menu_animate(self):
        if self.side_menu.width() <= SIDE_MENU_WIDTH + 10:
            start_value = SIDE_MENU_WIDTH
            end_value = SIDE_MENU_EXTENDED_WIDTH
        elif self.side_menu.width() >= SIDE_MENU_WIDTH + 10:
            start_value = SIDE_MENU_EXTENDED_WIDTH
            end_value = SIDE_MENU_WIDTH
        else:
            return

        self.animation1 = QtCore.QPropertyAnimation(self.side_menu, b'maximumWidth')
        self.animation1.setDuration(500)
        self.animation1.setStartValue(start_value)
        self.animation1.setEndValue(end_value)
        self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self.animation1.start()

        self.animation2 = QtCore.QPropertyAnimation(self.side_menu, b'minimumWidth')
        self.animation2.setDuration(500)
        self.animation2.setStartValue(start_value)
        self.animation2.setEndValue(end_value)
        self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self.animation2.start()

    def mousePressEvent(self, event):
        if event.x() > SIDE_MENU_EXTENDED_WIDTH and self.side_menu.width() >= SIDE_MENU_WIDTH + 10:
            self.side_menu_animate()
        super().mousePressEvent(event)
