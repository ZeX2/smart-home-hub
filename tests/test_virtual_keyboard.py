import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PySide6 import QtCore, QtTest, QtWidgets # type: ignore
except:
    from PySide2 import QtCore, QtTest, QtWidgets # type: ignore

from common_widgets.virtual_keyboard import VirtualKeyboard

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

class VirtualKeyboardTest(unittest.TestCase):

    def setUp(self):
        self.window = QtWidgets.QWidget()
        self.window.setFixedSize(800, 480)
        self.search_bar = QtWidgets.QLineEdit(self.window)
        completer = QtWidgets.QCompleter(['Chalmers', 'Chalmers Tvärgata', 'Chalmersplatsen', 'Chapmans Torg',
                                          'Charlottendal', 'Chalmers Johanneberg', 'Järntorget'])
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        self.keyboard = VirtualKeyboard(self.window)
        self.keyboard.setGeometry(0, 260, 800, 220)
        self.keyboard.attach(self.search_bar)
        self.window.show()
        QtTest.QTest.qWaitForWindowExposed(self.window)

    def tearDown(self):
        self.window.close()

    def tap(self, widget):
        # Through the window, so Qt routes the touch the way it does on the screen (popups included)
        pos = widget.mapTo(self.window, widget.rect().center())
        QtTest.QTest.mouseClick(self.window.windowHandle(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, pos)
        app.processEvents()

    def key(self, text):
        # Visible only, ⌫ / ⏎ / Klar exist on both pages
        return next(b for b in self.keyboard.findChildren(QtWidgets.QPushButton)
                    if b.text().replace('&&', '&') == text and b.isVisible())

    def test_tap_search_bar_types_and_closes(self):
        self.assertFalse(self.keyboard.isVisible())
        self.tap(self.search_bar)
        self.assertTrue(self.keyboard.isVisible())
        for text in ['j', 'ä', 'r', '⌫', ' ']:
            self.tap(self.key(text))
        self.assertEqual(self.search_bar.text(), 'jä ')
        self.tap(self.key('Klar'))
        self.assertFalse(self.keyboard.isVisible())

    def test_shift_types_one_capital(self):
        self.tap(self.search_bar)
        self.tap(self.key('⇧'))
        self.tap(self.key('Å'))
        self.tap(self.key('s'))
        self.assertEqual(self.search_bar.text(), 'Ås')

    def test_symbol_page_and_enter(self):
        entered = []
        self.search_bar.returnPressed.connect(lambda: entered.append(self.search_bar.text()))
        self.tap(self.search_bar)
        self.tap(self.key('123'))
        self.assertEqual(self.key('&').text(), '&&') # Shows as "&" rather than an empty key
        for text in ['4', '@', '&', '€', 'abc', 'q', '⏎']:
            self.tap(self.key(text))
        self.assertEqual(entered, ['4@&€q'])

    def test_suggestions_do_not_swallow_taps(self):
        self.tap(self.search_bar)
        for text in ['c', 'h', 'a']:
            self.tap(self.key(text))
        popup = self.search_bar.completer().popup()
        self.assertEqual(self.search_bar.text(), 'cha')
        self.assertTrue(popup.isVisible())

        # More matches than fit, yet the list must end above the keyboard (it would hide keys otherwise)
        popup_bottom = popup.mapToGlobal(QtCore.QPoint(0, popup.height())).y()
        keyboard_top = self.keyboard.mapToGlobal(QtCore.QPoint(0, 0)).y()
        self.assertLess(popup_bottom, keyboard_top)

        # Picking a suggestion fills in the name and closes the keyboard
        rect = popup.visualRect(popup.model().index(0, 0))
        QtTest.QTest.mouseClick(popup.viewport(), QtCore.Qt.LeftButton, QtCore.Qt.NoModifier, rect.center())
        self.assertEqual(self.search_bar.text(), 'Chalmers')
        self.assertFalse(self.keyboard.isVisible())

if __name__ == '__main__':
    unittest.main()
