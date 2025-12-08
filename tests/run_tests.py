import unittest
import sys

loader = unittest.TestLoader()
suite = loader.discover('tests')

runner = unittest.TextTestRunner()
result = runner.run(suite)

# Exit with 1 if tests fail
sys.exit(0 if result.wasSuccessful() else 1)
