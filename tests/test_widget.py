import unittest
import unittest.mock
from twidgets.core.base import Widget, Dimensions


class TestWidget(unittest.TestCase):
    @unittest.mock.patch('curses.initscr', return_value=unittest.mock.MagicMock())
    def test_widget_draw_disabled(self, mock_initscr: unittest.mock.MagicMock) -> None:
        stdscr = mock_initscr()
        dim = Dimensions(5, 5, 0, 0)
        config = unittest.mock.MagicMock()
        config.enabled = False
        w = Widget('name', 'title', config, unittest.mock.MagicMock(), None, dim, stdscr)
        w.draw(unittest.mock.MagicMock())  # Should not raise

    def test_toggle_help_mode(self) -> None:
        config = unittest.mock.MagicMock()
        config.enabled = True
        w = Widget('name', 'title', config, unittest.mock.MagicMock(), None, Dimensions(1, 1, 0, 0),
                   unittest.mock.MagicMock())
        self.assertFalse(w.help_mode)
        w.toggle_help_mode()
        self.assertTrue(w.help_mode)
        w.toggle_help_mode()
        self.assertFalse(w.help_mode)
