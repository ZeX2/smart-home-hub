import sys

from hub import SmartHomeHub

from PySide2.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    smart_home_hub = SmartHomeHub()
    sys.exit(app.exec_())
