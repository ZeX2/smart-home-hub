import urllib.request

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PySide2 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets

from .spotify_tokens import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

SCOPES = ['user-library-read', 'user-read-recently-played',
    'user-modify-playback-state', 'user-read-currently-playing',
    'user-read-playback-state', 'app-remote-control']

class SpotifyUi(QtWidgets.QWidget):

    def setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        top_spacer = QtWidgets.QSpacerItem(10, 20)
        self.layout.addSpacerItem(top_spacer)

        self.album_cover_layout = QtWidgets.QHBoxLayout()
        left_spacer = QtWidgets.QSpacerItem(20, 10, hData=QtWidgets.QSizePolicy.Expanding)
        right_spacer = QtWidgets.QSpacerItem(20, 10, hData=QtWidgets.QSizePolicy.Expanding)
        #self.album_cover_scene = QtWidgets.QGraphicsScene()
        #self.album_cover = QtWidgets.QGraphicsView(self.album_cover_scene)
        #self.album_cover.setFixedSize(200, 200)
        #self.setStyleSheet('QGraphicsView { background: red; border: 1px rounded black}')
        self.album_cover = QtWidgets.QLabel()
        self.album_cover.setStyleSheet('background: red; border: 1px rounded black')
        self.album_cover.setFixedSize(200, 200)
        self.album_cover.setScaledContents(True)
        self.album_cover_layout.addSpacerItem(left_spacer)
        self.album_cover_layout.addWidget(self.album_cover)
        self.album_cover_layout.addSpacerItem(right_spacer)
        self.layout.addLayout(self.album_cover_layout)

class SpotifyWidget(SpotifyUi):

    def __init__(self):
        super().__init__()
        self.setup_ui()

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                client_secret=CLIENT_SECRET,
                                                redirect_uri=REDIRECT_URI,
                                                scope=' '.join(SCOPES)))

        self.check_and_update_currently_playing()

    def check_and_update_currently_playing(self):
        curr_playing = self.sp.currently_playing()
        if curr_playing and curr_playing['is_playing']:
            album_cover_url = curr_playing['item']['album']['images'][0]['url']
            album_cover_data = urllib.request.urlopen(album_cover_url).read()
            image = QtGui.QImage()
            image.loadFromData(album_cover_data)
            self.album_cover.setPixmap(QtGui.QPixmap(image))
            #self.album_cover_scene.clear()
            #elf.album_cover_scene.addPixmap(QtGui.QPixmap(str(album_cover_data)))
            #self.album_cover_scene.update()
