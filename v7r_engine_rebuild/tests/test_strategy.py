# 架空データのみ。Strategy Team の動作確認。
import unittest
from engine.strategy import strategy_summary


def hz(a, wpr=0.5, svi=0.5):
    return {"step1": {"ability_score": a}, "step2": {"wpr_score": wpr},
            "step3": {"overall_svi": svi}}


class Strategy(unittest.TestCase):
    def setUp(self):
        self.horses = {1: hz(0.9), 2: hz(0.5, wpr=None)}
        self.rt = {"status": "ok", "horses": {
            1: {"redteam_severity": "高", "accepted_loss_categories": ["pace_failure", "fit_failure"],
                "unknown_risks": ["x"]},
            2: {"redteam_severity": "低", "accepted_loss_categories": [], "unknown_risks": []}}}

    def test_pass_recommends_step13(self):
        r = strategy_summary(self.horses, {"order": [1, 2]}, {"most_wins": 1}, {}, self.rt, "pass")
        self.assertEqual(r["推奨判断"], "STEP13（予測固定）へ進む")

    def test_fail_does_not_recommend_step13(self):
        r = strategy_summary(self.horses, {"order": [1, 2]}, {"most_wins": 1}, {}, self.rt, "fail（後続へ進めない）")
        self.assertIn("進まない", r["推奨判断"])

    def test_risk_lists_high_horse(self):
        r = strategy_summary(self.horses, {"order": [1, 2]}, {"most_wins": 1}, {}, self.rt, "pass")
        self.assertTrue(any("馬1" in x and "高" in x for x in r["最大リスク"]))

    def test_top_and_most_mismatch_is_flagged(self):
        r = strategy_summary(self.horses, {"order": [1, 2]}, {"most_wins": 2}, {}, self.rt, "review")
        self.assertTrue(any("説明が必要" in x for x in r["最重要論点"]))

    def test_most_trusted_is_highest_coverage(self):
        r = strategy_summary(self.horses, {"order": [1, 2]}, {"most_wins": 1}, {}, self.rt, "pass")
        self.assertEqual(r["最も信頼できる評価"]["最も信頼できる評価"], "能力順位（STEP1）")


if __name__ == "__main__":
    unittest.main()
