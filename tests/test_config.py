import unittest
import unittest.mock
from twidgets.core.base import Config


class TestConfig(unittest.TestCase):
    def test_missing_fields_logs_error(self) -> None:
        log_messages = unittest.mock.MagicMock()
        Config('file_name', log_messages)
        log_messages.add_log_message.assert_called()
