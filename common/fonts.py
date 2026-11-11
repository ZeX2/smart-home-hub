import glob
import os

try:
    from PySide6 import QtGui # type: ignore
except:
    from PySide2 import QtGui # type: ignore

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
DEFAULT_PIXEL_SIZE = 13

def load_app_font(app):
    for path in sorted(glob.glob(os.path.join(FONT_DIR, '*.ttf'))):
        families = QtGui.QFontDatabase.applicationFontFamilies(QtGui.QFontDatabase.addApplicationFont(path))
        if families:
            font = QtGui.QFont(families[0])
            font.setPixelSize(DEFAULT_PIXEL_SIZE)
            app.setFont(font)

def app_font(pixel_size, bold=False):
    font = QtGui.QFont()
    font.setPixelSize(pixel_size)
    font.setBold(bold)
    return font
