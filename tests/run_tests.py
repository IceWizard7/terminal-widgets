import unittest

if __name__ == '__main__':
    # Discover all tests in the current directory (tests/)
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='.', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
