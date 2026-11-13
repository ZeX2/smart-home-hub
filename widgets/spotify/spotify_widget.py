import os
import json
import time
import urllib.request
from datetime import date, timedelta, datetime

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError, CacheFileHandler

try:
    from PySide6 import QtGui, QtCore, QtWidgets # type: ignore
except:
    from PySide2 import QtGui, QtCore, QtWidgets # type: ignore

from common_widgets.buttons import QLabelButton
from common.qthreading import Worker, get_thread_pool
from common.art import art_folder
from .spotify_tokens import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

SPOTIFY_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(SPOTIFY_WIDGET_DIR, 'config.json')
art = art_folder('spotify')
SCOPES = ['user-library-read', 'user-read-recently-played',
    'user-modify-playback-state', 'user-read-currently-playing',
    'user-read-playback-state', 'app-remote-control']

def format_time(ms, duration_ms):
    # str(timedelta) gives '0:03:05'; cut it to '03:05', or '0:42' for tracks under a minute
    time_str = str(timedelta(seconds=int(ms/1000)))
    if duration_ms >= 60*60*1000:
        return time_str
    elif duration_ms < 60*1000:
        return time_str[3:]
    return time_str[2:]

def download_album_cover(url):
    image = QtGui.QImage()
    try:
        image.loadFromData(urllib.request.urlopen(url, timeout=5).read())
    except Exception as e:
        print(f'SpotifyWidget: failed to download album cover: {e}')
    return url, image

def pick_album_cover_url(item, thumbnail=False):
    images = item.get('album', {}).get('images')
    if not images:
        return None
    # Covers come widest first (640, 300, 64 px); 300 px is plenty for the 200 px label, 64 px for a thumbnail
    return images[-1 if thumbnail else min(1, len(images) - 1)]['url']

class MarqueeLabel(QtWidgets.QLabel):
    '''One line of text that scrolls right to left in a loop when it doesn't fit'''
    GAP = 40  # px between the end of the text and the start of its next lap

    def __init__(self, text=''):
        super().__init__(text)
        self.offset = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.scroll_step)

    def minimumSizeHint(self):
        # Long text scrolls, so it never needs to widen the layout
        return QtCore.QSize(0, super().minimumSizeHint().height())

    def setText(self, text):
        super().setText(text)
        self.offset = 0
        self.update_scrolling()

    def text_width(self):
        self.ensurePolished()  # measure with the style sheet's font, not the default one
        return self.fontMetrics().horizontalAdvance(self.text())

    def update_scrolling(self):
        if self.isVisible() and self.text_width() > self.contentsRect().width():
            if not self.timer.isActive():
                self.timer.start(30)
        else:
            self.timer.stop()
            self.offset = 0
        self.update()

    def scroll_step(self):
        self.offset = (self.offset + 1) % (self.text_width() + self.GAP)
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scrolling()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_scrolling()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()  # no point redrawing on the screensaver or another tab

    def paintEvent(self, event):
        if not self.timer.isActive():
            return super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        rect, text_width = self.contentsRect(), self.text_width()
        # Two copies, so the next lap follows the first one in
        for x in (rect.x() - self.offset, rect.x() - self.offset + text_width + self.GAP):
            painter.drawText(QtCore.QRect(x, rect.y(), text_width, rect.height()),
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self.text())

class QueueRow(QtWidgets.QWidget):

    def __init__(self, text, cover):
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        self.cover = QtWidgets.QLabel()
        self.cover.setFixedSize(32, 32)
        self.cover.setScaledContents(True)
        self.cover.setPixmap(cover)
        self.label = MarqueeLabel(text)
        layout.addWidget(self.cover)
        layout.addWidget(self.label)

# Inspo: https://chowdera.com/2021/05/20210506082607288s.html#4__281
# https://programmer.group/python-developing-music-player-pyqt-making-music-player-main-interface.html
# https://stackoverflow.com/questions/44264852/pyside-pyqt-overlay-widget

class StayOpenMenu(QtWidgets.QMenu):
    # Tapping a row runs it without closing the menu, so a device switch can be watched; tapping outside closes it
    def mouseReleaseEvent(self, event):
        action = self.activeAction()
        if action and action.isEnabled():
            action.trigger()
        else:
            super().mouseReleaseEvent(event)

class SpotifyUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        top_spacer = QtWidgets.QSpacerItem(10, 20)
        self.layout.addSpacerItem(top_spacer)

        # The queue button opens the queue on the right, squeezing the cover and song info to the left
        self.now_playing_and_queue_layout = QtWidgets.QHBoxLayout()
        now_playing_page = QtWidgets.QWidget()
        now_playing_layout = QtWidgets.QVBoxLayout(now_playing_page)
        now_playing_layout.setContentsMargins(0, 0, 0, 0)

        self.album_cover_layout = QtWidgets.QHBoxLayout()
        left_spacer = QtWidgets.QSpacerItem(20, 10, hData=QtWidgets.QSizePolicy.Expanding)
        right_spacer = QtWidgets.QSpacerItem(20, 10, hData=QtWidgets.QSizePolicy.Expanding)
        self.album_cover = QtWidgets.QLabel()
        self.album_cover.setStyleSheet('background: red; border: 1px rounded black')
        self.album_cover.setFixedSize(200, 200)
        self.album_cover.setScaledContents(True)
        self.album_cover_layout.addSpacerItem(left_spacer)
        self.album_cover_layout.addWidget(self.album_cover)
        self.album_cover_layout.addSpacerItem(right_spacer)
        # Spare height: a quarter above the cover, a quarter between it and the title, the rest below the artist
        now_playing_layout.addStretch(1)
        now_playing_layout.addLayout(self.album_cover_layout)

        self.title_label = MarqueeLabel()
        self.title_label.setStyleSheet('color: black; font-size: 20px;')
        self.artist_label = MarqueeLabel()
        self.artist_label.setStyleSheet('color: gray; font-size: 15px;')
        now_playing_layout.addStretch(1)
        for label in (self.title_label, self.artist_label):
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setMaximumWidth(360)  # longer text scrolls instead of stretching across the screen; fits beside the queue
            now_playing_layout.addWidget(label, alignment=QtCore.Qt.AlignHCenter)
        now_playing_layout.addStretch(2)
        self.now_playing_and_queue_layout.addWidget(now_playing_page, 11)

        self.queue_page = QtWidgets.QWidget()
        queue_layout = QtWidgets.QVBoxLayout(self.queue_page)
        queue_layout.setContentsMargins(0, 0, 0, 15)  # a gap above the controls
        self.queue_context_label = QtWidgets.QLabel()
        self.queue_list = QtWidgets.QListWidget()
        self.queue_list.setStyleSheet('''
            QListWidget { border: none; }
            QListWidget QLabel { font-size: 13px; }
        ''')
        self.queue_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.queue_list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.queue_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)  # long rows scroll their text instead
        self.queue_list.itemClicked.connect(self.queue_item_clicked)
        # Drag to scroll, since the touchscreen has no scroll wheel
        QtWidgets.QScroller.grabGesture(self.queue_list.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)
        queue_layout.addWidget(self.queue_context_label)
        queue_layout.addWidget(self.queue_list)
        self.queue_page.hide()
        self.now_playing_and_queue_layout.addWidget(self.queue_page, 9)
        self.layout.addLayout(self.now_playing_and_queue_layout, 1)  # takes the spare height, keeping the controls at the bottom

        self.music_controls_layout = QtWidgets.QHBoxLayout()
        outer_left_spacer = QtWidgets.QSpacerItem(100, 10)
        outer_right_spacer = QtWidgets.QSpacerItem(100, 10)
        left_spacer = QtWidgets.QSpacerItem(20, 10)
        right_spacer = QtWidgets.QSpacerItem(20, 10)
        self.shuffle_button = QLabelButton(art('shuffle_off.png'))
        self.shuffle_button.clicked.connect(self.shuffle_button_clicked)
        self.shuffle_button.setFixedSize(25, 25)
        self.prev_button = QLabelButton(art('prev_btn.svg'))
        self.prev_button.clicked.connect(self.prev_button_clicked)
        self.prev_button.setFixedSize(40, 30)
        self.play_button = QLabelButton(art('play_btn.svg'))
        self.play_button.clicked.connect(self.play_button_clicked)
        self.play_button.setFixedSize(35, 35)
        self.next_button = QLabelButton(art('next_btn.svg'))
        self.next_button.clicked.connect(self.next_button_clicked)
        self.next_button.setFixedSize(40, 30)
        self.repeat_button = QLabelButton(art('repeat_off.png'))
        self.repeat_button.clicked.connect(self.repeat_button_clicked)
        self.repeat_button.setFixedSize(25, 25)
        self.queue_button = QLabelButton(art('music_queue.png'))
        self.queue_button.clicked.connect(self.queue_button_clicked)
        self.queue_button.setFixedSize(25, 25)
        self.device_button = QLabelButton(art('device_off.png'))
        self.device_button.clicked.connect(self.device_button_clicked)
        self.device_button.setFixedSize(25, 25)
        self.device_menu = StayOpenMenu(self)
        self.device_menu.setStyleSheet('''
            QMenu { font-size: 15px; }
            QMenu::item { padding: 10px 25px; }
            QMenu::item:default { color: #19a149; }  /* the device in use, green like the on icons */
        ''')
        # Tapping outside only closes the menu, rather than also pressing the control underneath
        self.device_menu.setAttribute(QtCore.Qt.WA_NoMouseReplay)
        self.music_controls_layout.addSpacerItem(outer_left_spacer)
        # The device button and its gap mirror the queue button and its gap on the right, so play stays centered
        self.music_controls_layout.addWidget(self.device_button)
        self.music_controls_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 10))
        self.music_controls_layout.addWidget(self.shuffle_button)
        self.music_controls_layout.addSpacerItem(left_spacer)
        self.music_controls_layout.addWidget(self.prev_button)
        self.music_controls_layout.addWidget(self.play_button)
        self.music_controls_layout.addWidget(self.next_button)
        self.music_controls_layout.addSpacerItem(right_spacer)
        self.music_controls_layout.addWidget(self.repeat_button)
        self.music_controls_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 10))
        self.music_controls_layout.addWidget(self.queue_button)
        self.music_controls_layout.addSpacerItem(outer_right_spacer)
        self.layout.addLayout(self.music_controls_layout)

        self.music_slider_layout = QtWidgets.QHBoxLayout()
        left_spacer = QtWidgets.QSpacerItem(50, 10)
        right_spacer = QtWidgets.QSpacerItem(50, 10)
        self.progress_time_label = QtWidgets.QLabel('00:00')
        self.duration_time_label = QtWidgets.QLabel('00:00')
        self.music_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.music_slider.sliderReleased.connect(self.music_slider_released)
        self.music_slider.sliderMoved.connect(self.music_slider_moved)
        self.music_slider.sliderPressed.connect(self.music_slider_started_moving)
        self.music_slider.setMinimum(0)
        self.music_slider.setStyleSheet('''
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: gray;
                border-radius: 4px;
                height: 10px;
            }

            QSlider::groove:horizontal:hover {
                border: 1px solid #bbb;
                background: green;
                border-radius: 4px;
                height: 10px;
            }

            QSlider::sub-page:horizontal {
                border: 1px solid #777;
                background: white;
                height: 10px;
                border-radius: 4px;
            }

            QSlider::sub-page:horizontal:hover {
                border: 1px solid #777;
                background: green;
                height: 10px;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: none;
                border: none;
                color: none;
                width: 13px;
                margin-top: -2px;
                margin-bottom: -2px;
                margin-left: -2px;
                border-radius: 4px;
            }

            QSlider::handle:horizontal:hover {
                background: white;
                border: 1px solid #777;
                width: 13px;
                margin-top: -2px;
                margin-bottom: -2px;
                margin-left: -2px;
                border-radius: 4px;
            }
        ''')

        self.music_slider_layout.addSpacerItem(left_spacer)
        self.music_slider_layout.addWidget(self.progress_time_label)
        self.music_slider_layout.addWidget(self.music_slider)
        self.music_slider_layout.addWidget(self.duration_time_label)
        self.music_slider_layout.addSpacerItem(right_spacer)
        self.layout.addLayout(self.music_slider_layout)

class SpotifyWidget(SpotifyUi):

    def __init__(self):
        super().__init__()
        self.setup_ui()

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                client_secret=CLIENT_SECRET,
                                                redirect_uri=REDIRECT_URI,
                                                scope=' '.join(SCOPES),
                                                open_browser=True,
                                                cache_handler=CacheFileHandler(cache_path=os.path.join(SPOTIFY_WIDGET_DIR, 'tokens.txt'))))

        self.thread_pool = get_thread_pool()
        # Spotify calls run one at a time, so a skip always lands before the poll that checks it
        self.spotify_pool = QtCore.QThreadPool()
        self.spotify_pool.setMaxThreadCount(1)

        self.curr_playing_last_updated = None
        self.curr_playing = {}
        self.poll_pending = False
        self.commands_sent = 0
        self.skipped_from = []
        self.skip_deadline = 0
        self.device_switch_deadline = 0
        self.switching_to = None
        self.queue = []
        self.queue_for = None
        self.context_names = {}
        try:
            with open(CONFIG_PATH, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, ValueError):
            self.config = {}
        # Remembered across restarts, since it's only measured when a song ends on its own
        self.crossfade_ms = self.config.get('crossfade_ms', 0)
        self.album_cover_url = None
        self.album_covers = {}
        self.album_cover_downloads = set()
        self.no_album_cover = QtGui.QPixmap(art('no_album_cover.png'))

        self.music_slider_timer = QtCore.QTimer()
        self.music_slider_timer.timeout.connect(self.update_progress_time)

        self.curr_playing_timer = QtCore.QTimer()
        self.curr_playing_timer.timeout.connect(self.update_currently_playing)

        # One-off polls between the regular ones: shortly after a skip, and right when the song ends
        self.extra_poll_timer = QtCore.QTimer()
        self.extra_poll_timer.setSingleShot(True)
        self.extra_poll_timer.timeout.connect(self.update_currently_playing)

        # Rechecks the device list while a switch is pending, so the open menu shows how it went
        self.device_poll_timer = QtCore.QTimer()
        self.device_poll_timer.setSingleShot(True)
        self.device_poll_timer.timeout.connect(self.refresh_devices)

        self.update_currently_playing()
        self.curr_playing_timer.start(3*1000)

    def run_spotify(self, fn, *args, on_result=None):
        worker = Worker(fn, *args)
        if on_result:
            worker.signals.result.connect(on_result)
        self.spotify_pool.start(worker)

    def send_command(self, fn, *args):
        self.commands_sent += 1
        self.run_spotify(fn, *args)

    def update_currently_playing(self):
        if self.visibleRegion().isEmpty() or self.poll_pending:
            return
        self.poll_pending = True
        self.run_spotify(self.fetch_playback, self.commands_sent, on_result=self.playback_received)

    def fetch_playback(self, commands_sent):
        try:
            return commands_sent, self.sp.current_playback()
        except Exception as e:
            print(f'SpotifyWidget: failed to get current playback: {e}')
            if isinstance(e, SpotifyOauthError) and e.error == 'invalid_grant':
                # spotipy only re-runs the browser login when no token is cached
                cache_path = self.sp.auth_manager.cache_handler.cache_path
                if os.path.exists(cache_path):
                    os.remove(cache_path)
            return commands_sent, None

    def playback_received(self, result):
        commands_sent, curr_playing = result
        self.poll_pending = False
        curr_playing = curr_playing or {}

        skipping = time.monotonic() < self.skip_deadline
        if commands_sent != self.commands_sent or (skipping and (curr_playing.get('item') or {}).get('uri') in self.skipped_from):
            # Asked before the latest tap, or Spotify hasn't switched tracks yet: keep what's on screen
            if skipping:
                self.extra_poll_timer.start(300)
            return
        self.skip_deadline = 0

        prev_playing, prev_updated = self.curr_playing, self.curr_playing_last_updated
        self.curr_playing = curr_playing
        self.curr_playing_last_updated = datetime.now()

        # Spotify reports the old device for a moment after a switch; if the switch failed, this puts the real one back
        if time.monotonic() >= self.device_switch_deadline:
            self.update_device_button(self.curr_playing.get('device'))

        if not self.curr_playing or not self.curr_playing['item']:
            return

        prev_item = prev_playing.get('item')
        if prev_item and prev_playing['is_playing'] and not skipping and prev_item['uri'] != self.curr_playing['item']['uri']:
            # The API never says if crossfade is on, so measure how early Spotify left the last song
            switched_at = self.curr_playing_last_updated - timedelta(milliseconds=self.curr_playing['progress_ms'])
            prev_progress_ms = prev_playing['progress_ms'] + (switched_at - prev_updated).total_seconds()*1000
            gap_ms = prev_item['duration_ms'] - prev_progress_ms
            # Over Spotify's 12 s max crossfade means it was skipped from another device; under -1 s means
            # more than one song played while this page was hidden (screensaver, other tab), or it was paused.
            # Whole seconds, like the setting, so the length doesn't jitter from song to song
            if -1000 <= gap_ms <= 12_000:
                crossfade_ms = max(round(gap_ms / 1000), 0) * 1000
                if crossfade_ms != self.crossfade_ms:
                    self.crossfade_ms = self.config['crossfade_ms'] = crossfade_ms
                    self.save_config()

        if self.curr_playing['item']['uri'] != self.queue_for:
            # Ask what plays next so Next can show it without waiting for Spotify.
            # shortcut: asked once per song, so songs queued from another device mid-song aren't
            # shown early (the polls after the skip still catch them); refetch every poll if that bothers
            self.queue, self.queue_for = [], self.curr_playing['item']['uri']
            self.run_spotify(self.fetch_queue, self.commands_sent, on_result=self.queue_received)

        if not self.music_slider.isSliderDown():
            self.update_progress_time()

        if self.curr_playing['is_playing']:
            self.play_button.setPixmap(QtGui.QPixmap(art('pause_btn.svg')))
        else:
            self.play_button.setPixmap(QtGui.QPixmap(art('play_btn.svg')))
        self.update_shuffle_button()
        self.update_repeat_button()

        if not self.curr_playing['is_playing'] or self.music_slider.isSliderDown():
            self.music_slider_timer.stop()
        else:
            self.music_slider_timer.start(1000)

        if self.curr_playing['is_playing']:
            # Ask again right after the song ends instead of up to 3 s later
            remaining_ms = self.shown_duration_ms() - self.curr_playing['progress_ms']
            self.extra_poll_timer.start(max(remaining_ms, 0) + 500)
        else:
            self.extra_poll_timer.stop()

        if not self.curr_playing['item'] == prev_playing.get('item'):
            self.update_song_information()

    def fetch_queue(self, commands_sent):
        return commands_sent, self.sp.queue()['queue']

    def queue_received(self, result):
        commands_sent, queue = result
        if commands_sent != self.commands_sent:
            self.queue_for = None  # a tap since then may have changed what's next, so ask again on the next poll
            return
        self.queue = queue
        self.update_queue_list()
        next_cover_url = pick_album_cover_url(queue[0]) if queue else None
        if next_cover_url and next_cover_url not in self.album_covers:
            self.start_album_cover_download(next_cover_url)

    def device_button_clicked(self):
        self.run_spotify(self.fetch_devices, on_result=self.devices_received)

    def fetch_devices(self):
        try:
            return self.sp.devices()['devices']
        except Exception as e:
            print(f'SpotifyWidget: failed to get devices: {e}')
            return []

    def devices_received(self, devices):
        if self.visibleRegion().isEmpty():
            return  # left the page while waiting for Spotify
        switching = self.switching_to and time.monotonic() < self.device_switch_deadline
        self.device_menu.clear()
        for device in devices:
            name = device['name'].replace('&', '&&')  # a lone & would underline the next letter
            if device['id'] == self.switching_to and not device['is_active']:
                name += ' (switching…)' if switching else " (couldn't switch)"
            action = self.device_menu.addAction(name)
            action.setEnabled(bool(device['id']) and not device['is_restricted'])  # Spotify refuses commands to restricted devices
            # PySide may call it with or without the checked argument
            action.triggered.connect(lambda *_, device=device, action=action: self.device_chosen(device, action))
            if device['is_active']:
                # Marked as the default to color it green; checkable rows would get a tick in the Mac style
                self.device_menu.setDefaultAction(action)
        if not devices:
            self.device_menu.addAction('No devices found').setEnabled(False)

        if switching and not any(d['id'] == self.switching_to and d['is_active'] for d in devices):
            self.device_poll_timer.start(1000)
        else:
            self.switching_to = None
        self.place_device_menu()

    def place_device_menu(self):
        # Centered above the button, with a gap that also clears the taller play button
        size = self.device_menu.sizeHint()
        top_center = self.device_button.mapToGlobal(QtCore.QPoint(self.device_button.width() // 2, -10))
        pos = top_center - QtCore.QPoint(size.width() // 2, size.height())
        if self.device_menu.isVisible():
            self.device_menu.setGeometry(QtCore.QRect(pos, size))
        else:
            self.device_menu.popup(pos)

    def refresh_devices(self):
        if self.device_menu.isVisible():
            self.run_spotify(self.fetch_devices, on_result=self.devices_refreshed)

    def devices_refreshed(self, devices):
        if self.device_menu.isVisible():  # not reopened if it was closed while waiting
            self.devices_received(devices)

    def device_chosen(self, device, action):
        action.setText(device['name'].replace('&', '&&') + ' (switching…)')
        self.place_device_menu()
        self.switching_to = device['id']
        self.update_device_button(device)
        self.device_switch_deadline = time.monotonic() + 5
        # Keep playing or paused as it is; with nothing playing, starting it is why a device was picked
        self.send_command(self.sp.transfer_playback, device['id'], self.curr_playing.get('is_playing', True))
        self.device_poll_timer.start(1000)

    def update_device_button(self, device):
        icon = 'device_on.png' if device else 'device_off.png'
        self.device_button.setPixmap(QtGui.QPixmap(art(icon)))

    def hideEvent(self, event):
        super().hideEvent(event)
        self.device_menu.close()  # it's its own window, so it would stay on top of the screensaver

    def queue_button_clicked(self):
        self.queue_page.setVisible(self.queue_page.isHidden())
        if not self.queue_page.isHidden():
            self.update_queue_list()
            # Otherwise only fetched once per song, so ask again for anything queued since
            self.run_spotify(self.fetch_queue, self.commands_sent, on_result=self.queue_received)

    def update_queue_list(self):
        if self.queue_page.isHidden():
            return

        context = self.curr_playing.get('context')
        if context and context['uri'] not in self.context_names:
            self.context_names[context['uri']] = None  # asked for, so it's only fetched once
            self.run_spotify(self.fetch_context_name, context, on_result=self.context_name_received)
        if context:
            heading, name = 'PLAYING FROM:', self.context_names[context['uri']] or ''
        else:
            heading, name = 'UP NEXT', ''
        self.queue_context_label.setText(f'''
            <span style="color: gray; font-size: 11px;">{heading}</span>
            <span style="color: black; font-size: 15px;">{name}</span>
        ''')

        self.queue_list.clear()
        for item in self.queue:
            artists = ', '.join(artist['name'] for artist in item.get('artists', []))
            cover_url = pick_album_cover_url(item, thumbnail=True)
            row = QueueRow(f'{item["name"]} – {artists}' if artists else item['name'],
                           self.album_covers.get(cover_url, self.no_album_cover))
            list_item = QtWidgets.QListWidgetItem()
            list_item.setData(QtCore.Qt.UserRole, cover_url)  # so the cover can find its row when it arrives
            # No width of its own, so rows fit the list's width and long ones scroll their text
            list_item.setSizeHint(QtCore.QSize(0, row.sizeHint().height()))
            self.queue_list.addItem(list_item)
            self.queue_list.setItemWidget(list_item, row)
            if cover_url and cover_url not in self.album_covers:
                self.start_album_cover_download(cover_url)

    def queue_item_clicked(self, list_item):
        index = self.queue_list.row(list_item)
        if index >= len(self.queue):
            return  # the song just changed and the new queue isn't here yet
        item, jumped_over = self.queue[index], [song['uri'] for song in self.queue[:index]]
        self.queue = self.queue[index + 1:]
        context = self.curr_playing.get('context')
        self.skip_track(lambda: self.play_from_queue(context, item['uri'], index), item, jumped_over)

    def play_from_queue(self, context, uri, index):
        # Only playlists and albums can start at a given song
        if context and context['type'] in ('playlist', 'album'):
            try:
                self.sp.start_playback(context_uri=context['uri'], offset={'uri': uri})
                return
            except spotipy.SpotifyException as e:
                print(f'SpotifyWidget: could not play {uri} in {context["uri"]}, skipping ahead instead: {e}')
        # Songs queued by hand aren't in the playlist, so skip to them like Spotify's own queue does
        for _ in range(index + 1):
            self.sp.next_track()

    def fetch_context_name(self, context):
        # Playback only says what kind of thing is playing and its URI, so look up the name
        try:
            if context['type'] == 'collection':
                name = 'Liked Songs'
            elif context['type'] == 'playlist':
                name = self.sp.playlist(context['uri'], fields='name')['name']
            elif context['type'] in ('album', 'artist', 'show'):
                name = getattr(self.sp, context['type'])(context['uri'])['name']  # spotipy names its getters after the types
            else:
                name = None
        except Exception as e:
            print(f'SpotifyWidget: failed to get the name of {context["uri"]}: {e}')
            name = None
        return context['uri'], name

    def context_name_received(self, result):
        uri, name = result
        self.context_names[uri] = name
        self.update_queue_list()

    def update_song_information(self):
        title = self.curr_playing['item']['name']
        artists = [artist['name'] for artist in self.curr_playing['item']['artists']]

        self.title_label.setText(title)
        self.artist_label.setText(', '.join(artists))

        self.album_cover_url = pick_album_cover_url(self.curr_playing['item'])
        if self.album_cover_url in self.album_covers:
            self.album_cover.setPixmap(self.album_covers[self.album_cover_url])
        elif self.album_cover_url:
            self.start_album_cover_download(self.album_cover_url)
        else:
            self.album_cover.setPixmap(self.no_album_cover)

        duration_ms = self.shown_duration_ms()
        self.music_slider.setMaximum(duration_ms)
        self.duration_time_label.setText(format_time(duration_ms, duration_ms))

    def start_album_cover_download(self, url):
        if url in self.album_cover_downloads:
            return  # the queue list redraws often, so don't fetch the same cover twice
        self.album_cover_downloads.add(url)
        worker = Worker(download_album_cover, url)
        worker.signals.result.connect(self.album_cover_downloaded)
        self.thread_pool.start(worker)

    def album_cover_downloaded(self, result):
        url, image = result
        self.album_cover_downloads.discard(url)
        pixmap = QtGui.QPixmap.fromImage(image)
        if pixmap.isNull():
            pixmap = self.no_album_cover
        else:
            if len(self.album_covers) >= 50:
                self.album_covers.pop(next(iter(self.album_covers)))  # drop the oldest
            self.album_covers[url] = pixmap

        for row in range(self.queue_list.count()):
            if self.queue_list.item(row).data(QtCore.Qt.UserRole) == url:
                self.queue_list.itemWidget(self.queue_list.item(row)).cover.setPixmap(pixmap)
        if url == self.album_cover_url:  # unless skipped to another song while this downloaded
            self.album_cover.setPixmap(pixmap)

    def save_config(self):
        # Write a temp file and swap it in, so a power cut mid-write can't leave a half config.json
        with open(CONFIG_PATH + '.tmp', 'w') as f:
            f.write(json.dumps(self.config, indent=4, sort_keys=True))
        os.replace(CONFIG_PATH + '.tmp', CONFIG_PATH)

    def shown_duration_ms(self):
        # With crossfade on, Spotify moves on this much before the end, so that's where the song ends here too
        return self.curr_playing['item']['duration_ms'] - self.crossfade_ms

    def update_progress_time(self, progress_ms=None):
        duration_ms = self.shown_duration_ms()
        if progress_ms is None:
            delta_time = datetime.now() - self.curr_playing_last_updated
            progress_ms = delta_time.total_seconds()*1000 + self.curr_playing['progress_ms']
        progress_ms = min(progress_ms, duration_ms)

        self.music_slider.setValue(progress_ms)
        self.progress_time_label.setText(format_time(progress_ms, duration_ms))

    def update_shuffle_button(self):
        icon = 'shuffle_on.png' if self.curr_playing.get('shuffle_state') else 'shuffle_off.png'
        self.shuffle_button.setPixmap(QtGui.QPixmap(art(icon)))

    def update_repeat_button(self):
        icon = {'context': 'repeat_on.png', 'track': 'reapeat_once.png'}.get(self.curr_playing.get('repeat_state'), 'repeat_off.png')
        self.repeat_button.setPixmap(QtGui.QPixmap(art(icon)))

    def music_slider_started_moving(self):
        self.music_slider_timer.stop()

    def music_slider_released(self):
        self.curr_playing['progress_ms'] = self.music_slider.value()
        self.curr_playing_last_updated = datetime.now()
        self.send_command(self.sp.seek_track, self.music_slider.value())
        self.music_slider_timer.start(1000)
    
    def music_slider_moved(self):
        duration_ms = self.curr_playing['item']['duration_ms']
        progress_ms = self.music_slider.value()
        self.progress_time_label.setText(format_time(progress_ms, duration_ms))
    
    def play_button_clicked(self):
        if self.curr_playing.get('is_playing'):
            self.music_slider_timer.stop()
            self.curr_playing['is_playing'] = False
            self.send_command(self.sp.pause_playback)
            self.play_button.setPixmap(QtGui.QPixmap(art('play_btn.svg')))
        else:
            self.music_slider_timer.start(1000)
            self.curr_playing['is_playing'] = True
            self.send_command(self.sp.start_playback)
            self.play_button.setPixmap(QtGui.QPixmap(art('pause_btn.svg')))
    
    def next_button_clicked(self):
        self.skip_track(self.sp.next_track, self.queue.pop(0) if self.queue else None)

    def prev_button_clicked(self):
        # The queue only lists what comes after the current song
        self.queue, self.queue_for = [], None
        self.skip_track(self.sp.previous_track)

    def skip_track(self, skip_fn, next_item=None, jumped_over=()):
        if time.monotonic() >= self.skip_deadline:
            self.skipped_from = []
        # Every song skipped past counts, so a double tap or a jump down the queue doesn't flash the songs in between
        self.skipped_from += [(self.curr_playing.get('item') or {}).get('uri'), *jumped_over]
        # Plus time for each skip, in case the jump has to skip ahead one song at a time
        self.skip_deadline = time.monotonic() + 3 + 0.3*len(jumped_over)
        if self.curr_playing.get('item'):
            # Restart the slider now so its timer doesn't run on from the old song's position
            self.curr_playing['progress_ms'] = 0
            self.curr_playing_last_updated = datetime.now()
            if next_item and next_item.get('type') == 'track':
                # Show the queued song right away; the polls after the skip correct it if Spotify plays another
                self.curr_playing['item'] = next_item
                self.update_song_information()
            self.update_progress_time()
        self.update_queue_list()
        self.send_command(skip_fn)
        self.update_currently_playing()

    def shuffle_button_clicked(self):
        if not self.curr_playing:
            return
        self.curr_playing['shuffle_state'] = not self.curr_playing.get('shuffle_state')
        self.update_shuffle_button()
        self.queue_for = None  # shuffling changes what plays next, so the next poll fetches the queue again
        self.send_command(self.sp.shuffle, self.curr_playing['shuffle_state'])

    def repeat_button_clicked(self):
        if not self.curr_playing:
            return
        # Same order as Spotify's own button: off, the whole playlist or album, this song
        next_state = {'off': 'context', 'context': 'track', 'track': 'off'}
        self.curr_playing['repeat_state'] = next_state[self.curr_playing.get('repeat_state', 'off')]
        self.update_repeat_button()
        self.send_command(self.sp.repeat, self.curr_playing['repeat_state'])
