# 架空データのみ。STEP6 の動作確認。
import unittest
from engine.step6 import step6_redteam


def horse(ability=0.9, wpr=0.8, style=0.5, pace_dmg=0.2, fit=0.8, jockey=0.8):
    return {"step1": {"ability_score": ability, "recent_level": None, "growth": None},
            "step2": {"wpr_score": wpr, "allowed_range": (1, 5)},
            "step3": {"style_index": style, "pace_benefit": 0.5, "pace_damage": pace_dmg,
                      "distance_fit": fit, "course_fit": fit, "track_fit": fit, "warnings": []},
            "step4": {"positioning_reproducibility": jockey, "timing_reproducibility": None,
                      "course_fit": None, "horse_fit": None, "tactical_flexibility": None,
                      "warnings": []}}


def route(status="complete", wins=True, losses=True, opp=None):
    met = {"text": "x", "sources": ["STEP1"], "value": 1, "met": True}
    return {"status": status, "ideal_pace": "ミドル",
            "wins": [met] if wins else [], "losses": [met] if losses else [],
            "key_opponents": opp or []}


class Step6(unittest.TestCase):
    def test_blocked_when_step5_incomplete(self):
        r = step6_redteam("ミドル", {1: horse()}, {1: route(status="incomplete")}, {})
        self.assertEqual(r["status"], "blocked")

    def test_blocked_when_conditions_empty(self):
        r = step6_redteam("ミドル", {1: horse()}, {1: route(wins=False)}, {})
        self.assertEqual(r["status"], "blocked")

    def test_pace_collapse_accepted_when_damage_high(self):
        r = step6_redteam("ミドル", {1: horse(pace_dmg=0.7)}, {1: route()}, {})
        cps = {c["category"]: c for c in r["horses"][1]["counterpoints"]}
        self.assertEqual(cps["pace_failure"]["kind"], "accepted")
        self.assertIn("pace_failure", r["horses"][1]["accepted_loss_categories"])

    def test_missing_style_gives_unknown_not_accepted(self):
        r = step6_redteam("ミドル", {1: horse(style=None)}, {1: route()}, {})
        cps = {c["category"]: c for c in r["horses"][1]["counterpoints"]}
        self.assertEqual(cps["position_failure"]["kind"], "unknown")

    def test_fit_failure_accepted(self):
        h = horse(fit=0.3)
        r = step6_redteam("ミドル", {1: h}, {1: route()}, {})
        self.assertEqual(r["horses"][1]["redteam_severity"], "medium")

    def test_severity_from_category_count(self):
        h = horse(pace_dmg=0.7, fit=0.3)
        r = step6_redteam("ミドル", {1: h}, {1: route()}, {})
        self.assertIn(r["horses"][1]["redteam_severity"], ("medium", "high"))
        self.assertGreaterEqual(len(r["horses"][1]["accepted_loss_categories"]), 2)

    def test_top_ability_downgrade_only_with_all_three_accepted(self):
        h = horse(ability=0.95, pace_dmg=0.7, style=0.1, wpr=0.3)
        r = step6_redteam("ハイ", {1: h}, {1: route(opp=[])}, {})
        audit = r["horses"]["top_ability_audit"]
        self.assertEqual(audit["horse"], 1)
        self.assertFalse(audit["downgrade_eligible"])  # 相手が成立していない


if __name__ == "__main__":
    unittest.main()
