import unittest
from scripts.peq_optimizer import route_multichannel_layout

class TestMultichannelRouting(unittest.TestCase):
    def test_stereo_2_0_layout(self):
        channels = route_multichannel_layout("STEREO_2_0")
        self.assertEqual(channels, ["Front_L", "Front_R"])

    def test_surround_5_1_layout(self):
        channels = route_multichannel_layout("SURROUND_5_1")
        expected = ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer"]
        self.assertEqual(channels, expected)

    def test_surround_7_1_layout(self):
        channels = route_multichannel_layout("SURROUND_7_1")
        expected = ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer"]
        self.assertEqual(channels, expected)

if __name__ == "__main__":
    unittest.main()
