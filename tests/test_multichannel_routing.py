import unittest
from scripts.peq_optimizer import route_multichannel_layout

class TestMultichannelRouting(unittest.TestCase):
    def test_mono_and_stereo(self):
        self.assertEqual(route_multichannel_layout("1.0"), ["Center"])
        self.assertEqual(route_multichannel_layout("2.0"), ["Front_L", "Front_R"])
        self.assertEqual(route_multichannel_layout("2.1"), ["Front_L", "Front_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("2.2"), ["Front_L", "Front_R", "Subwoofer_1", "Subwoofer_2"])

    def test_front_stage_and_quad(self):
        self.assertEqual(route_multichannel_layout("3.0"), ["Front_L", "Front_R", "Center"])
        self.assertEqual(route_multichannel_layout("3.1"), ["Front_L", "Front_R", "Center", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("4.0"), ["Front_L", "Front_R", "Surround_L", "Surround_R"])
        self.assertEqual(route_multichannel_layout("4.1"), ["Front_L", "Front_R", "Surround_L", "Surround_R", "Subwoofer"])

    def test_5_x_surround(self):
        self.assertEqual(route_multichannel_layout("5.0"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R"])
        self.assertEqual(route_multichannel_layout("5.1"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("5.2"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer_1", "Subwoofer_2"])

    def test_7_x_surround(self):
        self.assertEqual(route_multichannel_layout("7.0"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R"])
        self.assertEqual(route_multichannel_layout("7.1"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("7.2"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer_1", "Subwoofer_2"])

    def test_immersive_presence_height_atmos(self):
        self.assertEqual(route_multichannel_layout("5.1.2"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("5.1.4"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("7.1.2"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("7.1.4"), ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"])
        self.assertEqual(route_multichannel_layout("9.1.6"), ["Front_L", "Front_R", "Center", "Front_Wide_L", "Front_Wide_R", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Top_Middle_L", "Top_Middle_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"])

if __name__ == "__main__":
    unittest.main()
