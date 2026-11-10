import os
import sys
import shutil
import socket
import subprocess

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common.qthreading import Worker, get_thread_pool

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
REFRESH_MS = 5000
UNKNOWN = '–' # Shown on machines without the Linux /proc and /sys files, e.g. a Mac during development

def read_first(path):
    with open(path) as f:
        return f.read()

def format_duration(seconds):
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    return f'{days} d {hours} h {rest // 60} min' if days else f'{hours} h {rest // 60} min'

def cpu_temp(path='/sys/class/thermal/thermal_zone0/temp'):
    return f'{int(read_first(path)) / 1000:.1f} °C'

def memory(path='/proc/meminfo'):
    kb = {line.split(':')[0]: int(line.split()[1]) for line in read_first(path).splitlines()}
    used = kb['MemTotal'] - kb['MemAvailable']
    return f'{used / 1024**2:.1f} / {kb["MemTotal"] / 1024**2:.1f} GB'

def disk():
    usage = shutil.disk_usage('/')
    return f'{usage.used / 1024**3:.1f} / {usage.total / 1024**3:.1f} GB'

def uptime(path='/proc/uptime'):
    return format_duration(float(read_first(path).split()[0]))

def load():
    return ' '.join(f'{x:.2f}' for x in os.getloadavg())

def ip_address():
    # Connecting a UDP socket sends nothing, it only picks the interface that routes to the internet
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]

def wifi(path='/proc/net/wireless'):
    # Header is two lines, then e.g. "wlan0: 0000   58.  -52.  -256 ..." with link quality out of 70
    fields = read_first(path).splitlines()[2].split()
    return f'{float(fields[2]) / 70:.0%} ({float(fields[3]):.0f} dBm)'

SYSTEM_INFO = [('CPU temp', cpu_temp), ('Memory', memory), ('Disk', disk), ('Load', load),
               ('Uptime', uptime), ('IP address', ip_address), ('Wi-Fi', wifi)]

def system_info():
    info = {}
    for name, read in SYSTEM_INFO:
        try:
            info[name] = read()
        except Exception:
            info[name] = UNKNOWN
    return info

def git(*args):
    return subprocess.run(['git', '-C', REPO_DIR, *args], capture_output=True, text=True, timeout=60)

def pull_update():
    before = git('rev-parse', 'HEAD').stdout
    result = git('pull', '--ff-only')
    if result.returncode:
        return False, (result.stderr or result.stdout).strip().splitlines()[-1]
    if git('rev-parse', 'HEAD').stdout == before:
        return False, 'Already up to date'
    return True, 'Updated, restarting…'

class SettingsUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(30)

        info_box = QtWidgets.QGroupBox('System')
        info_layout = QtWidgets.QFormLayout(info_box)
        info_layout.setVerticalSpacing(14)
        self.info_labels = {}
        for name, _ in SYSTEM_INFO:
            self.info_labels[name] = QtWidgets.QLabel(UNKNOWN)
            info_layout.addRow(f'{name}:', self.info_labels[name])
        self.layout.addWidget(info_box, 1)

        maintenance_box = QtWidgets.QGroupBox('Maintenance')
        maintenance_layout = QtWidgets.QVBoxLayout(maintenance_box)
        maintenance_layout.setSpacing(10)
        self.update_button = QtWidgets.QPushButton('Update from git')
        self.restart_button = QtWidgets.QPushButton('Restart app')
        self.refresh_stops_button = QtWidgets.QPushButton('Refresh Västtrafik stops')
        self.reboot_button = QtWidgets.QPushButton('Reboot')
        self.shutdown_button = QtWidgets.QPushButton('Shut down')
        for button in [self.update_button, self.restart_button, self.refresh_stops_button, self.reboot_button, self.shutdown_button]:
            button.setMinimumHeight(48) # Finger sized
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            maintenance_layout.addWidget(button)
        self.status_label = QtWidgets.QLabel('')
        self.status_label.setWordWrap(True)
        maintenance_layout.addWidget(self.status_label)
        maintenance_layout.addStretch()
        self.layout.addWidget(maintenance_box, 1)

        self.setStyleSheet('''
            QGroupBox { font-size: 18px; font-weight: bold; }
            QLabel { font-size: 16px; font-weight: normal; }
            QPushButton { font-size: 16px; }
        ''')

class SettingsWidget(SettingsUi):

    def __init__(self, reseplaneraren):
        super().__init__()
        self.reseplaneraren = reseplaneraren
        self.setup_ui()

        self.info_timer = QtCore.QTimer(self)
        self.info_timer.setInterval(REFRESH_MS)
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start()

        self.update_button.clicked.connect(self.update_app)
        self.restart_button.clicked.connect(self.restart)
        self.refresh_stops_button.clicked.connect(self.refresh_stops)
        self.reboot_button.clicked.connect(lambda: self.power('Reboot', ['sudo', '-n', 'reboot']))
        self.shutdown_button.clicked.connect(lambda: self.power('Shut down', ['sudo', '-n', 'shutdown', '-h', 'now']))

    def tab_changed(self):
        self.update_info()

    def update_info(self):
        if not self.isVisible():
            return
        for name, value in system_info().items():
            self.info_labels[name].setText(value)

    def run(self, fn, on_result, *args):
        worker = Worker(fn, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(lambda error: self.status_label.setText(f'Failed: {error[1]}'))
        get_thread_pool().start(worker)

    def update_app(self):
        self.status_label.setText('Pulling…')
        self.run(pull_update, self.update_done)

    def update_done(self, result):
        changed, message = result
        self.status_label.setText(message)
        if changed:
            QtCore.QTimer.singleShot(1000, self.restart) # Let the message show first

    def restart(self):
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def refresh_stops(self):
        self.status_label.setText('Refreshing stops…')
        self.run(lambda: self.reseplaneraren.set_stops_data(force=True), self.stops_refreshed)

    def stops_refreshed(self, _):
        self.status_label.setText(f'{len(self.reseplaneraren.get_stop_names())} stops loaded, new names show in search after a restart')

    def power(self, action, command):
        answer = QtWidgets.QMessageBox.question(self, action, f'{action} the hub?')
        if answer != QtWidgets.QMessageBox.Yes:
            return
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            self.status_label.setText(f'{action} failed: {result.stderr.strip()}')
