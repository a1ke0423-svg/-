# 架空データのみ。表示用の総合値の動作確認。
import unittest
from engine.overview import overview, DISPLAY_WEIGHTS


def base(**over):
    d = {"step1": {"ability_score": 0.8}, "step2": {"wpr_score": 0.5},
         "step3": {"distance_fit": 0.6, "course_fit": 0.4, "track_fit": None}}
    for k, v in over.items():
        d[k] = v
    return d


class Overview(unittest.TestCase):
    def test_equal_mean_of_available(self):
        r = overview(base())
        self.assertEqual(r["used_count"], 4)
        self.assertAlmostEqual(r["display_score"], round((0.8 + 0.6 + 0.4 + 0.5) / 4, 4))

    def test_missing_items_are_listed_not_filled(self):
        r = overview(base())
        self.assertIn("馬場適正", r["missing"])
        self.assertIn("気性", r["missing"])
        self.assertEqual(r["total_count"], 6)

    def test_track_fit_included_when_present(self):
        d = base()
        d["step3"]["track_fit"] = 1.0
        r = overview(d)
        self.assertEqual(r["used_count"], 5)
        self.assertNotIn("馬場適正", r["missing"])

    def test_no_items_gives_none(self):
        r = overview({"step1": {"ability_score": None}, "step2": {"wpr_score": None},
                      "step3": {"distance_fit": None, "course_fit": None, "track_fit": None}})
        self.assertIsNone(r["display_score"])
        self.assertEqual(r["used_count"], 0)

    def test_weights_are_all_equal_and_documented(self):
        self.assertTrue(all(w == 1.0 for w in DISPLAY_WEIGHTS.values()))
        self.assertEqual(len(DISPLAY_WEIGHTS), 6)


if __name__ == "__main__":
    unittest.main()
