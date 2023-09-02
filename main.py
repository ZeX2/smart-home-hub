import sys

from hub import SmartHomeHub

try:
    from PySide6.QtWidgets import QApplication # type: ignore
except:
    from PySide2.QtWidgets import QApplication # type: ignore

if __name__ == "__main__":
    app = QApplication(sys.argv)
    smart_home_hub = SmartHomeHub()
    sys.exit(app.exec())
