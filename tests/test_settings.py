import os
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from widgets.settings import settings_widget as s

def temp_file(text):
    f = tempfile.NamedTemporaryFile('w', delete=False)
    f.write(text)
    f.close()
    return f.name

class SystemInfoTest(unittest.TestCase):

    def test_parsers(self):
        self.assertEqual(s.cpu_temp(temp_file('48312\n')), '48.3 °C')
        self.assertEqual(s.memory(temp_file('MemTotal: 4194304 kB\nMemFree: 1 kB\nMemAvailable: 3145728 kB\n')), '1.0 / 4.0 GB')
        self.assertEqual(s.uptime(temp_file('93784.12 1000.0\n')), '1 d 2 h 3 min')
        self.assertEqual(s.uptime(temp_file('3700.0 1.0\n')), '1 h 1 min')
        wireless = ('Inter-| sta-|   Quality        |   Discarded packets\n'
                    ' face | tus | link level noise |  nwid  crypt   frag\n'
                    ' wlan0: 0000   56.  -54.  -256        0      0      0\n')
        self.assertEqual(s.wifi(temp_file(wireless)), '80% (-54 dBm)')

    def test_missing_files_show_unknown(self):
        info = s.system_info()
        self.assertEqual([name for name, _ in s.SYSTEM_INFO], list(info))
        self.assertTrue(all(isinstance(value, str) and value for value in info.values()))

if __name__ == '__main__':
    unittest.main()
