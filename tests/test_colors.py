import unittest
from twidgets.core.base import RGBColor


class TestRGBColor(unittest.TestCase):
    def test_rgb_to_0_1000(self) -> None:
        color = RGBColor(255, 128, 0)
        self.assertEqual(color.rgb_to_0_1000(), (1000, 502, 0))

    def test_add_rgb_color_from_dict(self) -> None:
        color = RGBColor.add_rgb_color_from_dict({'r': 1, 'g': 2, 'b': 3})
        self.assertEqual((color.r, color.g, color.b), (1, 2, 3))
