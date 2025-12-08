import unittest
from twidgets.core.base import Dimensions


class TestDimensions(unittest.TestCase):
    def test_formatted(self) -> None:
        dim = Dimensions(10, 20, 1, 2)
        self.assertEqual(dim.formatted(), [10, 20, 1, 2])

    def test_within_borders_true(self) -> None:
        dim = Dimensions(5, 5, 1, 1)
        self.assertTrue(dim.within_borders(10, 10))

    def test_within_borders_false(self) -> None:
        dim = Dimensions(10, 10, 5, 5)
        self.assertFalse(dim.within_borders(10, 10))
