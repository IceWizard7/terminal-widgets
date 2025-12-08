import unittest
import unittest.mock
from twidgets.core.base import Widget, Dimensions, WidgetContainer


class TestWidgetContainer(unittest.TestCase):
    @unittest.mock.patch('curses.initscr', return_value=unittest.mock.MagicMock())
    def test_add_widget(self, mock_initscr: unittest.mock.MagicMock) -> None:
        stdscr = mock_initscr()
        container = WidgetContainer(stdscr, None, test_env=True)
        config = unittest.mock.MagicMock()
        config.enabled = True
        dim = Dimensions(1, 1, 0, 0)
        w = Widget('name', 'title', config, unittest.mock.MagicMock(), None, dim, stdscr)
        container.add_widget(w)
        self.assertIn(w, container.return_widgets())
