# 架空データのみ。STEP5 の動作確認。
import unittest
from engine.step5 import step5_routes, ideal_pace


def res(ability=0.9, wpr=0.8, style=0.2, pace_dmg=0.2, fit=0.8, step_num=0):
    return {"step1": {"ability_score": ability},
            "step2": {"wpr_score": wpr, "allowed_range": (1, 4)},
            "step3": {"style_index": style, "pace_benefit": 1 - style, "pace_damage": pace_dmg,
                      "distance_fit": fit, "course_fit": fit, "track_fit": fit}}


class Step5(unittest.TestCase):
    def test_ideal_pace_bands(self):
        self.assertEqual(ideal_pace(0.2), "スロー")
        self.assertEqual(ideal_pace(0.5), "ミドル")
        self.assertEqual(ideal_pace(0.8), "ハイ")
        self.assertIsNone(ideal_pace(None))

    def test_met_win_and_no_evidence_text_kept(self):
        r = step5_routes({1: res(ability=0.9)})[1]
        self.assertTrue(r["wins"][0]["met"])
        r2 = step5_routes({1: res(ability=0.6)})[1]
        self.assertFalse(r2["wins"][0]["met"])
        self.assertIn("根拠なし", r2["wins"][0]["text"])

    def test_lists_never_empty(self):
        r = step5_routes({1: res()})[1]
        self.assertGreater(len(r["wins"]), 0)
        self.assertGreater(len(r["losses"]), 0)

    def test_undetermined_input_marks_incomplete(self):
        r = step5_routes({1: res(ability=None)})[1]
        self.assertEqual(r["status"], "incomplete")
        self.assertTrue(any("判定不能" in c["text"] for c in r["wins"]))

    def test_pace_collapse_loss(self):
        r = step5_routes({1: res(pace_dmg=0.7)})[1]
        collapse = [c for c in r["losses"] if "展開被害" in c["text"]][0]
        self.assertTrue(collapse["met"])

    def test_key_opponents_need_close_ability_and_overlap(self):
        a = res(ability=0.80); b = res(ability=0.75); c = res(ability=0.30)
        out = step5_routes({1: a, 2: b, 3: c})
        self.assertIn(2, out[1]["key_opponents"])
        self.assertNotIn(3, out[1]["key_opponents"])

    def test_route_confidence_counts_seven_inputs(self):
        r = step5_routes({1: res()})[1]
        self.assertEqual(r["route_confidence"], 1.0)


if __name__ == "__main__":
    unittest.main()
