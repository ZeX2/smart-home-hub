import os
import sys
import tempfile
import types
import unittest
from datetime import timedelta
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
# The real tokens file is gitignored and not needed here
sys.modules['widgets.spotify.spotify_tokens'] = types.SimpleNamespace(
    CLIENT_ID='id', CLIENT_SECRET='secret', REDIRECT_URI='http://localhost:8888/callback')

try:
    from PySide6 import QtCore, QtGui, QtTest, QtWidgets # type: ignore
except:
    from PySide2 import QtCore, QtGui, QtTest, QtWidgets # type: ignore

import spotipy
from widgets.spotify.spotify_widget import MarqueeLabel, SpotifyWidget, art

def track(name):
    return {'type': 'track', 'uri': f'spotify:track:{name}', 'name': name, 'artists': [],
            'album': {'images': []}, 'duration_ms': 200_000}

def playback(name, progress_ms=0):
    return {'is_playing': True, 'progress_ms': progress_ms, 'item': track(name)}

def device(name, is_active=False, is_restricted=False):
    return {'id': f'{name}-id', 'name': name, 'is_active': is_active, 'is_restricted': is_restricted}

def shows_icon(button, icon):
    return button.pixmap().toImage() == QtGui.QPixmap(art(icon)).toImage()

class PollTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        config_path = mock.patch('widgets.spotify.spotify_widget.CONFIG_PATH', os.path.join(tmp_dir.name, 'config.json'))
        config_path.start()
        self.addCleanup(config_path.stop)

        self.widget = SpotifyWidget()
        self.widget.sp = mock.MagicMock()
        self.widget.thread_pool = mock.Mock()  # no cover downloads
        self.widget.playback_received((0, playback('Alpha', 50_000)))

    def tearDown(self):
        self.widget.spotify_pool.waitForDone()

    def test_old_song_after_skip_is_ignored_until_spotify_switches(self):
        self.widget.next_button_clicked()
        self.widget.playback_received((self.widget.commands_sent, playback('Alpha', 51_000)))
        self.assertEqual(self.widget.curr_playing['item']['name'], 'Alpha')
        self.assertEqual(self.widget.curr_playing['progress_ms'], 0)
        self.assertEqual(self.widget.extra_poll_timer.interval(), 300)

        self.widget.playback_received((self.widget.commands_sent, playback('Bravo')))
        self.assertEqual(self.widget.curr_playing['item']['name'], 'Bravo')

    def test_poll_sent_before_a_tap_is_ignored(self):
        self.widget.play_button_clicked()
        self.widget.playback_received((self.widget.commands_sent - 1, playback('Alpha', 51_000)))
        self.assertFalse(self.widget.curr_playing['is_playing'])

    def test_polls_again_when_the_song_ends(self):
        self.widget.playback_received((0, playback('Alpha', 199_000)))
        self.assertEqual(self.widget.extra_poll_timer.interval(), 1500)

    def test_next_shows_the_queued_song_right_away(self):
        self.widget.queue_received((self.widget.commands_sent, [track('Bravo')]))
        self.widget.next_button_clicked()
        self.assertIn('Bravo', self.widget.title_label.text())

        self.widget.playback_received((self.widget.commands_sent, playback('Alpha', 51_000)))
        self.assertIn('Bravo', self.widget.title_label.text())

    def test_double_tap_skips_the_song_in_between(self):
        self.widget.queue_received((self.widget.commands_sent, [track('Bravo'), track('Charlie')]))
        self.widget.next_button_clicked()
        self.widget.next_button_clicked()
        self.assertIn('Charlie', self.widget.title_label.text())

        self.widget.playback_received((self.widget.commands_sent, playback('Bravo')))
        self.assertIn('Charlie', self.widget.title_label.text())
        self.widget.playback_received((self.widget.commands_sent, playback('Charlie')))
        self.assertEqual(self.widget.curr_playing['item']['name'], 'Charlie')

    def test_queue_page_lists_the_queue_and_where_it_plays_from(self):
        self.widget.curr_playing['context'] = {'type': 'playlist', 'uri': 'spotify:playlist:party'}
        self.widget.queue_button_clicked()
        self.widget.queue_received((self.widget.commands_sent, [track('Bravo'), track('Charlie')]))
        self.widget.context_name_received(('spotify:playlist:party', 'Party Mix'))
        rows = [self.widget.queue_list.itemWidget(self.widget.queue_list.item(i)) for i in range(self.widget.queue_list.count())]
        self.assertEqual([row.label.text() for row in rows], ['Bravo', 'Charlie'])
        self.assertIn('PLAYING FROM:', self.widget.queue_context_label.text())
        self.assertIn('Party Mix', self.widget.queue_context_label.text())

        self.widget.next_button_clicked()
        self.assertEqual(self.widget.queue_list.count(), 1)

    def test_shuffle_and_repeat_buttons_send_the_next_state(self):
        self.widget.playback_received((0, {**playback('Alpha'), 'shuffle_state': False, 'repeat_state': 'off'}))
        self.widget.shuffle_button_clicked()
        self.widget.repeat_button_clicked()
        self.widget.repeat_button_clicked()

        # A poll sent before the taps can't undo them
        self.widget.playback_received((0, {**playback('Alpha'), 'shuffle_state': False, 'repeat_state': 'off'}))
        self.assertTrue(self.widget.curr_playing['shuffle_state'])
        self.assertEqual(self.widget.curr_playing['repeat_state'], 'track')

        self.widget.spotify_pool.waitForDone()
        self.widget.sp.shuffle.assert_called_once_with(True)
        self.assertEqual([call.args for call in self.widget.sp.repeat.call_args_list], [('context',), ('track',)])

    def open_queue(self, songs, context={'type': 'playlist', 'uri': 'spotify:playlist:party'}):
        self.widget.curr_playing['context'] = context
        self.widget.queue_button_clicked()
        self.widget.queue_received((self.widget.commands_sent, songs))

    def test_tapping_a_queued_song_plays_it(self):
        self.open_queue([track('Bravo'), track('Charlie'), track('Delta')])
        self.widget.queue_item_clicked(self.widget.queue_list.item(1))
        self.assertIn('Charlie', self.widget.title_label.text())
        self.assertEqual(self.widget.queue_list.count(), 1)

        # Spotify may report a song from before the jump for a moment
        self.widget.playback_received((self.widget.commands_sent, playback('Bravo')))
        self.assertIn('Charlie', self.widget.title_label.text())

        self.widget.spotify_pool.waitForDone()
        self.widget.sp.start_playback.assert_called_once_with(
            context_uri='spotify:playlist:party', offset={'uri': 'spotify:track:Charlie'})

    def test_song_queued_by_hand_is_reached_by_skipping(self):
        self.widget.sp.start_playback.side_effect = spotipy.SpotifyException(404, -1, 'Not in the playlist')
        self.open_queue([track('Bravo'), track('Charlie')])
        self.widget.queue_item_clicked(self.widget.queue_list.item(1))
        self.widget.spotify_pool.waitForDone()
        self.assertEqual(self.widget.sp.next_track.call_count, 2)

    def test_queue_shows_small_covers(self):
        song = track('Bravo')
        song['album']['images'] = [{'url': 'big'}, {'url': 'medium'}, {'url': 'small'}]
        self.open_queue([song])
        red = QtGui.QImage(64, 64, QtGui.QImage.Format_RGB32)
        red.fill(QtGui.QColor('red'))
        self.widget.album_cover_downloaded(('small', red))
        cover = self.widget.queue_list.itemWidget(self.widget.queue_list.item(0)).cover.pixmap().toImage()
        self.assertEqual(cover.pixelColor(20, 20), QtGui.QColor('red'))

    def test_measures_crossfade_when_a_song_ends_on_its_own(self):
        # Alpha (200 s) is at 193 s, and the next poll finds Bravo already 1 s in: Spotify left Alpha 8 s early
        self.widget.playback_received((0, playback('Alpha', 193_000)))
        self.widget.playback_received((0, playback('Bravo', 1_000)))
        self.assertEqual(self.widget.crossfade_ms, 8_000)
        self.assertEqual(self.widget.duration_time_label.text(), '03:12')
        self.assertEqual(self.widget.extra_poll_timer.interval(), 191_000 + 500)

    def test_crossfade_is_remembered_after_a_restart(self):
        self.widget.playback_received((0, playback('Alpha', 193_000)))
        self.widget.playback_received((0, playback('Bravo', 1_000)))
        self.assertEqual(SpotifyWidget().crossfade_ms, 8_000)

    def test_songs_played_while_hidden_dont_reset_crossfade(self):
        self.widget.crossfade_ms = 5_000
        # Ten minutes on the screensaver: Alpha and a few more songs played unseen
        self.widget.curr_playing_last_updated -= timedelta(minutes=10)
        self.widget.playback_received((0, playback('Delta', 100_000)))
        self.assertEqual(self.widget.crossfade_ms, 5_000)

    def test_skip_from_another_device_is_not_crossfade(self):
        self.widget.playback_received((0, playback('Bravo', 1_000)))
        self.assertEqual(self.widget.crossfade_ms, 0)
        self.assertEqual(self.widget.duration_time_label.text(), '03:20')

    def test_device_button_is_green_while_a_device_is_connected(self):
        self.assertTrue(shows_icon(self.widget.device_button, 'device_off.png'))
        self.widget.playback_received((0, {**playback('Alpha'), 'device': device('Kitchen')}))
        self.assertTrue(shows_icon(self.widget.device_button, 'device_on.png'))
        # Nothing active, like after a long pause
        self.widget.playback_received((0, None))
        self.assertTrue(shows_icon(self.widget.device_button, 'device_off.png'))

    def test_choosing_a_device_switches_to_it(self):
        self.widget.show()
        self.widget.devices_received([device('Kitchen', is_active=True), device('Phone')])
        kitchen, phone = self.widget.device_menu.actions()
        self.assertTrue(self.widget.device_menu.isVisible())
        self.assertEqual(self.widget.device_menu.defaultAction(), kitchen)  # styled green
        self.assertFalse(kitchen.isCheckable())  # no tick next to it

        # Reopened with nothing active, nothing stays green
        self.widget.devices_received([device('Kitchen'), device('Phone')])
        self.assertIsNone(self.widget.device_menu.defaultAction())
        kitchen, phone = self.widget.device_menu.actions()

        phone.trigger()
        self.widget.spotify_pool.waitForDone()
        self.widget.sp.transfer_playback.assert_called_once_with('Phone-id', True)

    def test_menu_stays_open_and_shows_how_the_switch_went(self):
        self.widget.show()
        self.widget.devices_received([device('Kitchen', is_active=True), device('Phone')])
        menu = self.widget.device_menu
        phone = menu.actions()[1]
        QtTest.QTest.mouseClick(menu, QtCore.Qt.LeftButton, pos=menu.actionGeometry(phone).center())
        self.assertTrue(menu.isVisible())
        self.assertEqual(phone.text(), 'Phone (switching…)')
        self.assertTrue(self.widget.device_poll_timer.isActive())

        self.widget.devices_received([device('Kitchen', is_active=True), device('Phone')])  # not yet
        self.assertEqual(menu.actions()[1].text(), 'Phone (switching…)')
        self.widget.devices_received([device('Kitchen'), device('Phone', is_active=True)])
        kitchen, phone = menu.actions()
        self.assertEqual(phone.text(), 'Phone')
        self.assertEqual(menu.defaultAction(), phone)  # green
        self.assertTrue(menu.isVisible())

    def test_switch_that_never_happens_says_so(self):
        self.widget.show()
        self.widget.devices_received([device('Kitchen', is_active=True), device('Phone')])
        self.widget.device_menu.actions()[1].trigger()
        self.widget.device_switch_deadline = 0
        self.widget.devices_received([device('Kitchen', is_active=True), device('Phone')])
        self.assertEqual(self.widget.device_menu.actions()[1].text(), "Phone (couldn't switch)")
        self.assertIsNone(self.widget.switching_to)

    def test_switching_while_paused_stays_paused(self):
        self.widget.playback_received((0, {**playback('Alpha'), 'is_playing': False}))
        self.widget.show()
        self.widget.devices_received([device('Phone')])
        self.widget.device_menu.actions()[0].trigger()
        self.widget.spotify_pool.waitForDone()
        self.widget.sp.transfer_playback.assert_called_once_with('Phone-id', False)

    def test_old_device_right_after_a_switch_is_ignored(self):
        self.widget.show()
        self.widget.devices_received([device('Phone')])
        self.widget.device_menu.actions()[0].trigger()
        # Spotify may still report nothing connected for a moment
        self.widget.playback_received((self.widget.commands_sent, None))
        self.assertTrue(shows_icon(self.widget.device_button, 'device_on.png'))

        # If it still does later, the switch failed, so show the truth
        self.widget.device_switch_deadline = 0
        self.widget.playback_received((self.widget.commands_sent, None))
        self.assertTrue(shows_icon(self.widget.device_button, 'device_off.png'))

    def test_device_menu_disables_what_cant_be_chosen(self):
        self.widget.show()
        self.widget.devices_received([device('Tom & Jerry'), device('TV', is_restricted=True)])
        tom_and_jerry, tv = self.widget.device_menu.actions()
        self.assertEqual(tom_and_jerry.text(), 'Tom && Jerry')
        self.assertTrue(tom_and_jerry.isEnabled())
        self.assertFalse(tv.isEnabled())

    def test_failed_device_lookup_says_none_found(self):
        self.widget.sp.devices.side_effect = spotipy.SpotifyException(500, -1, 'Down')
        self.widget.show()
        self.widget.devices_received(self.widget.fetch_devices())
        self.assertEqual([action.text() for action in self.widget.device_menu.actions()], ['No devices found'])
        self.assertFalse(self.widget.device_menu.actions()[0].isEnabled())

    def test_device_menu_closes_with_the_page(self):
        self.widget.show()
        self.widget.devices_received([device('Phone')])
        self.widget.hide()  # like when the screensaver comes on
        self.assertFalse(self.widget.device_menu.isVisible())

        # A list arriving after leaving the page doesn't open it either
        self.widget.devices_received([device('Phone')])
        self.assertFalse(self.widget.device_menu.isVisible())

class MarqueeLabelTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_scrolls_only_text_that_doesnt_fit(self):
        label = MarqueeLabel('Short')
        label.setFixedWidth(100)
        label.show()
        self.assertFalse(label.timer.isActive())

        label.setText('A song title far too long for a hundred pixels')
        self.assertTrue(label.timer.isActive())
        label.scroll_step()
        self.assertEqual(label.offset, 1)

        label.hide()
        self.assertFalse(label.timer.isActive())

if __name__ == '__main__':
    unittest.main()
