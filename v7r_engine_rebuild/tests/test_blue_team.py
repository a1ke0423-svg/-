# 架空データのみ。Blue Team の動作確認。
import unittest
from engine.blue_team import audit, audit_inputs, summary


def hz(a, wpr=0.5, dist=0.6, course=0.6, track=0.6, idx=0.5):
    return {"step1": {"ability_score": a}, "step2": {"wpr_score": wpr},
            "step3": {"distance_fit": dist, "course_fit": course, "track_fit": track, "style_index": idx},
            "step4": {}}


def base():
    horses = {1: hz(0.9), 2: hz(0.5)}
    step5 = {1: {"status": "complete"}, 2: {"status": "complete"}}
    redteam = {"status": "ok"}
    step7 = {"order": [1, 2]}
    step9 = {"most_wins": 1}
    step10 = {"horses": {1: {"win_prob": 0.5, "reproducibility_wpr": 0.5},
                         2: {"win_prob": 0.0, "reproducibility_wpr": 0.5}}}
    return horses, step5, redteam, step7, step9, step10


class BlueTeam(unittest.TestCase):
    def test_all_pass_when_consistent(self):
        items = audit(*base(), overview_missing={1: ["馬場適正"], 2: ["馬場適正"]})
        self.assertEqual(summary(items), "pass")

    def test_market_info_in_input_fails(self):
        items = audit_inputs({"horses": [{"odds": 3.2}]})
        self.assertEqual(items[0]["status"], "fail")

    def test_clean_input_passes(self):
        items = audit_inputs({"horses": [{"name": "架空"}]})
        self.assertEqual(items[0]["status"], "pass")

    def test_unknown_not_listed_as_missing_fails(self):
        horses, s5, rt, s7, s9, s10 = base()
        horses[1]["step3"]["distance_fit"] = None
        items = audit(horses, s5, rt, s7, s9, s10, overview_missing={1: [], 2: []})
        self.assertEqual([i for i in items if i["item"].startswith("4.")][0]["status"], "fail")

    def test_top_demotion_without_reason_fails(self):
        horses, s5, rt, _, s9, s10 = base()
        items = audit(horses, s5, rt, {"order": [2, 1]}, s9, s10, overview_missing={1: ["馬場適正"], 2: ["馬場適正"]})
        self.assertEqual(summary(items).split("（")[0], "fail")

    def test_scenario_vs_rank_mismatch_needs_review(self):
        horses, s5, rt, s7, _, s10 = base()
        items = audit(horses, s5, rt, s7, {"most_wins": 2}, s10, overview_missing={1: ["馬場適正"], 2: ["馬場適正"]})
        self.assertEqual(summary(items).split("（")[0], "review")

    def test_blocked_step6_is_fail(self):
        horses, s5, _, s7, s9, s10 = base()
        items = audit(horses, s5, {"status": "blocked", "reason": "x"}, s7, s9, s10,
                      overview_missing={1: ["馬場適正"], 2: ["馬場適正"]})
        self.assertEqual(summary(items).split("（")[0], "fail")


if __name__ == "__main__":
    unittest.main()
