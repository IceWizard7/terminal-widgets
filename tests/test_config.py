import unittest
import unittest.mock
from twidgets.core.base import Config


class TestConfig(unittest.TestCase):
    def test_missing_fields_logs_error(self) -> None:
        widget_container: unittest.mock.MagicMock = unittest.mock.MagicMock()
        _ = Config('file_name', widget_container, True, 'UnitTest')
        widget_container.log_messages.add_log_message.assert_called()
