import unittest
from engine import thresholds as T


class Ten(unittest.TestCase):
    def test_points_to_internal(self):
        self.assertAlmostEqual(T.WIN_ABILITY, 0.8)
        self.assertAlmostEqual(T.LOSE_ABILITY, 0.5)
        self.assertAlmostEqual(T.OPPONENT_GAP, 0.1)
        self.assertAlmostEqual(T.PACE_DAMAGE_COLLAPSE, 0.6)
        self.assertAlmostEqual(T.FIT_MIN, 0.5)

    def test_ban_boundaries(self):
        self.assertEqual(T.FRONT_MAX_BAN, 5)
        self.assertEqual(T.BACK_MIN_BAN, 12)


if __name__ == "__main__":
    unittest.main()
