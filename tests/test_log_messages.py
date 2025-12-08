import unittest
import unittest.mock
from twidgets.core.base import LogMessage, LogMessages, LogLevels


class TestLogMessages(unittest.TestCase):
    def test_add_and_contains_error(self) -> None:
        logs = LogMessages()
        logs.add_log_message(LogMessage('Error occurred', LogLevels.ERROR.key))
        self.assertTrue(logs.contains_error())

    def test_print_log_messages(self) -> None:
        logs = LogMessages([LogMessage('Info msg', LogLevels.INFO.key)])
        # Temporarily override print function with mock_print (-> does nothing)
        with unittest.mock.patch('builtins.print') as mock_print:
            logs.print_log_messages('Heading\n')
            mock_print.assert_called()  # Check that print was called
