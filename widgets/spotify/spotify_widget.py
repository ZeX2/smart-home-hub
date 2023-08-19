import os
import urllib.request
from datetime import date, timedelta, datetime

import spotipy
from spotipy.oauth2 import SpotifyOAuth

try:
    from PySide6 import QtGui, QtCore, QtWidgets
except:
    from PySide2 import QtGui, QtCore, QtWidgets

from .spotify_tokens import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

SPOTIFY_WIDGET_DIR = os.path.dirname(os.path.realpath(__file__))
SCOPES = ['user-library-read', 'user-read-recently-played',
    'user-modify-playback-state', 'user-read-currently-playing',
    'user-read-playback-state', 'app-remote-control']

# Inspo: https://chowdera.com/2021/05/20210506082607288s.html#4__281
# https://programmer.group/python-developing-music-player-pyqt-making-music-player-main-interface.html
# https://stackoverflow.com/questions/44264852/pyside-pyqt-overlay-widget

class QLabelButton(QtWidgets.QLabel):
    clicked = QtCore.Signal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        QtWidgets.QLabel.mousePressEvent(self, event)

class SpotifyUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)

        top_spacer = QtWidgets.QSpacerItem(10, 20)
        self.layout.addSpacerItem(top_spacer)

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
        self.layout.addLayout(self.album_cover_layout)

        self.song_info_label = QtWidgets.QLabel()
        self.layout.addWidget(self.song_info_label)

        self.music_controls_layout = QtWidgets.QHBoxLayout()
        outer_left_spacer = QtWidgets.QSpacerItem(100, 10)
        outer_right_spacer = QtWidgets.QSpacerItem(100, 10)
        left_spacer = QtWidgets.QSpacerItem(20, 10)
        right_spacer = QtWidgets.QSpacerItem(20, 10)
        self.shuffle_button = QLabelButton()
        self.shuffle_button.clicked.connect(self.shuffle_button_clicked)
        self.shuffle_button.setFixedSize(25, 25)
        self.shuffle_button.setScaledContents(True)
        self.shuffle_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'shuffle_off.png')))
        self.prev_button = QLabelButton()
        self.prev_button.clicked.connect(self.prev_button_clicked)
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.setScaledContents(True)
        self.prev_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'prev_btn.png')))
        self.play_button = QLabelButton()
        self.play_button.clicked.connect(self.play_button_clicked)
        self.play_button.setFixedSize(35, 35)
        self.play_button.setScaledContents(True)
        self.play_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'play_btn.png')))
        self.next_button = QLabelButton()
        self.next_button.clicked.connect(self.next_button_clicked)
        self.next_button.setFixedSize(40, 30)
        self.next_button.setScaledContents(True)
        self.next_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'next_btn.png')))
        self.repeat_button = QLabelButton()
        self.repeat_button.clicked.connect(self.repeat_button_clicked)
        self.repeat_button.setFixedSize(25, 25)
        self.repeat_button.setScaledContents(True)
        self.repeat_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'repeat_off.png')))
        self.music_controls_layout.addSpacerItem(outer_left_spacer)
        self.music_controls_layout.addWidget(self.shuffle_button)
        self.music_controls_layout.addSpacerItem(left_spacer)
        self.music_controls_layout.addWidget(self.prev_button)
        self.music_controls_layout.addWidget(self.play_button)
        self.music_controls_layout.addWidget(self.next_button)
        self.music_controls_layout.addSpacerItem(right_spacer)
        self.music_controls_layout.addWidget(self.repeat_button)
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
                                                cache_path=os.path.join(SPOTIFY_WIDGET_DIR, 'tokens.txt')))

        self.curr_playing_last_updated = None
        self.curr_playing = {}

        self.music_slider_timer = QtCore.QTimer()
        self.music_slider_timer.timeout.connect(self.update_progress_time)

        self.curr_playing_timer = QtCore.QTimer()
        self.curr_playing_timer.timeout.connect(self.update_currently_playing)

        self.update_currently_playing()
        self.curr_playing_timer.start(3*1000)

    def update_currently_playing(self):
        prev_playing = self.curr_playing
        curr_playing = self.sp.current_playback()
        self.curr_playing = {} if not curr_playing else curr_playing
        self.curr_playing_last_updated = datetime.now()

        if not self.curr_playing or not self.curr_playing['item']:
            return

        if not self.music_slider.isSliderDown():
            self.update_progress_time()

        if self.curr_playing['is_playing']:
            self.play_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'pause_btn.png')))
        else:
            self.play_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'play_btn.png')))

        if not self.curr_playing['is_playing'] or self.music_slider.isSliderDown():
            self.music_slider_timer.stop()
        else:
            self.music_slider_timer.start(1000)

        if not self.curr_playing['item'] == prev_playing.get('item'):
            self.update_song_information()

    def update_song_information(self):
        title = self.curr_playing['item']['name']
        artists = [artist['name'] for artist in self.curr_playing['item']['artists']]

        self.song_info_label.setText(f'''
            <p style="color: black; font-family: Verdana; font-size: 20px; text-align: center;">{title}<p>
            <p style="color: gray; font-family: Verdana; font-size: 15px; text-align: center;">{", ".join(artists)}<p>
        ''')

        try:
            album_cover_url = self.curr_playing['item']['album']['images'][0]['url']
            album_cover_data = urllib.request.urlopen(album_cover_url).read()
            image = QtGui.QImage()
            image.loadFromData(album_cover_data)
            self.album_cover.setPixmap(QtGui.QPixmap(image))
        except:
            self.album_cover.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'no_album_cover.png')))

        duration_ms = self.curr_playing['item']['duration_ms']
        self.music_slider.setMaximum(duration_ms)

        duration_str = str(timedelta(seconds=int(duration_ms/1000)))
        if duration_ms >= 60*60*1000:
            self.duration_time_label.setText(duration_str)
        elif duration_ms < 60*1000:
            self.duration_time_label.setText(duration_str[3:])
        else:
            self.duration_time_label.setText(duration_str[2:])

    def update_progress_time(self, progress_ms=None):
        duration_ms = self.curr_playing['item']['duration_ms']
        if not progress_ms:
            delta_time = datetime.now() - self.curr_playing_last_updated
            progress_ms = delta_time.total_seconds()*1000 + self.curr_playing['progress_ms']

        self.music_slider.setValue(progress_ms)

        progress_str = str(timedelta(seconds=int(progress_ms/1000)))
        if duration_ms >= 60*60*1000:
            self.progress_time_label.setText(progress_str)
        elif duration_ms < 60*1000:
            self.progress_time_label.setText(progress_str[3:])
        else:
            self.progress_time_label.setText(progress_str[2:])

        if duration_ms - progress_ms < 1500:
            self.update_currently_playing()

    def update_shuffle_button(self):
        pass

    def update_repeat_button(self):
        pass

    def music_slider_started_moving(self):
        self.music_slider_timer.stop()

    def music_slider_released(self):
        self.curr_playing['progress_ms'] = self.music_slider.value()
        self.curr_playing_last_updated = datetime.now()
        self.sp.seek_track(self.music_slider.value())
        self.music_slider_timer.start(1000)
    
    def music_slider_moved(self):
        duration_ms = self.curr_playing['item']['duration_ms']
        progress_ms = self.music_slider.value()

        progress_str = str(timedelta(seconds=int(progress_ms/1000)))
        if duration_ms >= 60*60*1000:
            self.progress_time_label.setText(progress_str)
        elif duration_ms < 60*1000:
            self.progress_time_label.setText(progress_str[3:])
        else:
            self.progress_time_label.setText(progress_str[2:])
    
    def play_button_clicked(self):
        if self.curr_playing.get('is_playing'):
            self.music_slider_timer.stop()
            self.curr_playing['is_playing'] = False
            self.sp.pause_playback()
            self.play_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'play_btn.png')))
        else:
            self.music_slider_timer.start(1000)
            self.curr_playing['is_playing'] = True
            self.sp.start_playback()
            self.play_button.setPixmap(QtGui.QPixmap(os.path.join(SPOTIFY_WIDGET_DIR, 'pause_btn.png')))
    
    def next_button_clicked(self):
        self.sp.next_track()
        self.update_progress_time(0)
        self.update_currently_playing()
    
    def prev_button_clicked(self):
        self.sp.previous_track()
        self.update_progress_time(0)
        self.update_currently_playing()

    def shuffle_button_clicked(self):
        pass

    def repeat_button_clicked(self):
        pass
