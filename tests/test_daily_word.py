import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6 import QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtCore, QtWidgets # type: ignore

from widgets.daily_word.daily_word_widget import DailyWordWidget

class FakeDailyWordApi():
    def __init__(self, fail=False):
        self.fail = fail

    def get_eng_word_and_def(self):
        if self.fail:
            raise Exception('offline')
        return 'Alpha', 'first'

    def get_swe_word_and_def(self):
        return 'Beta', 'andra'

class DailyWordTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        # get_thread_pool() takes the pool from the main window
        cls.window = QtWidgets.QMainWindow()
        cls.window.thread_pool = QtCore.QThreadPool()

    def wait_for_word(self):
        self.window.thread_pool.waitForDone()
        self.app.processEvents()

    def test_word_loads_in_the_background(self):
        widget = DailyWordWidget(FakeDailyWordApi())
        self.wait_for_word()
        self.assertEqual(widget.title_label.text(), 'Word of the Day')
        self.assertEqual(widget.definition_label.text(), 'Alpha: first')

    def test_late_answer_for_the_other_language_is_ignored(self):
        widget = DailyWordWidget(FakeDailyWordApi())
        widget.combo_box.setCurrentText('SWE')
        self.wait_for_word()
        widget.set_word('ENG', ('Alpha', 'first'))
        self.assertEqual(widget.title_label.text(), 'Dagens Ord')
        self.assertEqual(widget.definition_label.text(), 'Beta: andra')

    def test_failure_shows_a_message(self):
        widget = DailyWordWidget(FakeDailyWordApi(fail=True))
        self.wait_for_word()
        self.assertEqual(widget.definition_label.text(), 'Could not load the word of the day.')

if __name__ == '__main__':
    unittest.main()
