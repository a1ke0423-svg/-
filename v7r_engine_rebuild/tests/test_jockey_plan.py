# 架空データのみ。騎手の戦術案の動作確認。
import unittest
from engine.jockey_plan import jockey_plan


EMPTY4 = {"positioning_reproducibility": None, "timing_reproducibility": None,
          "course_fit": None, "horse_fit": None, "tactical_flexibility": None}


class Plan(unittest.TestCase):
    def test_aim_from_allowed_range(self):
        p = jockey_plan("架空", {"allowed_range": (3, 9)}, "ミドル", "ミドル", EMPTY4)
        self.assertEqual(p["aim_position"], "3〜9番手で進める")

    def test_aim_unknown_when_no_range(self):
        p = jockey_plan("架空", {"allowed_range": None}, "ミドル", "ミドル", EMPTY4)
        self.assertTrue(p["aim_position"].startswith("不明"))

    def test_pace_match_and_mismatch(self):
        same = jockey_plan("架空", {"allowed_range": (1, 2)}, "ハイ", "ハイ", EMPTY4)
        self.assertIn("一致", same["pace_fit"])
        diff = jockey_plan("架空", {"allowed_range": (1, 2)}, "スロー", "ハイ", EMPTY4)
        self.assertIn("ずれる", diff["pace_fit"])

    def test_missing_jockey_metric_is_unknown(self):
        p = jockey_plan("架空", {"allowed_range": (1, 2)}, "ミドル", "ミドル", EMPTY4)
        self.assertTrue(all(v == "不明" for v in p["jockey_metrics"].values()))

    def test_no_name_based_bonus(self):
        p = jockey_plan("架空", {"allowed_range": (1, 2)}, "ミドル", "ミドル", EMPTY4)
        self.assertNotIn("有名", str(p))


if __name__ == "__main__":
    unittest.main()
