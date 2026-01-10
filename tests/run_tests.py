import unittest
import sys

if __name__ == '__main__':
    # Discover all tests in the current directory (tests/)
    loader: unittest.TestLoader = unittest.TestLoader()
    suite: unittest.TestSuite = loader.discover(start_dir='.', pattern='test_*.py')

    runner: unittest.TextTestRunner = unittest.TextTestRunner(verbosity=2)
    result: unittest.TextTestResult = runner.run(suite)

    # Exit with code 1 if any tests failed, so CI job fails
    sys.exit(0 if result.wasSuccessful() else 1)
