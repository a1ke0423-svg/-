# 架空データのみ。9 シナリオの動作確認。
import unittest
from engine.step9 import step9_scenarios, PACES, OUTCOMES


def h(a, idx):
    return {"step1": {"ability_score": a}, "step3": {"style_index": idx}}


class Nine(unittest.TestCase):
    def test_nine_scenarios(self):
        r = step9_scenarios({1: h(0.8, 0.5), 2: h(0.7, 0.5)}, [1, 2])
        self.assertEqual(len(r["scenarios"]), 9)
        pairs = {(s["pace"], s["outcome"]) for s in r["scenarios"]}
        self.assertEqual(pairs, {(p, o) for p in PACES for o in OUTCOMES})

    def test_deterministic(self):
        horses = {1: h(0.8, 0.3), 2: h(0.8, 0.7)}
        a = step9_scenarios(horses, [1, 2])
        b = step9_scenarios(horses, [1, 2])
        self.assertEqual(a, b)

    def test_front_outcome_favours_front_runner(self):
        horses = {1: h(0.5, 0.1), 2: h(0.5, 0.9)}  # 1 は前、2 は後ろ（能力は同じ）
        r = step9_scenarios(horses, [1, 2])
        front = [s for s in r["scenarios"] if s["outcome"] == "前残り"]
        self.assertTrue(all(s["winner"] == 1 for s in front))

    def test_missing_input_goes_last_as_unknown(self):
        horses = {1: h(None, 0.5), 2: h(0.5, 0.5)}
        r = step9_scenarios(horses, [2, 1])
        self.assertEqual(r["scenarios"][0]["order"][-1], 1)
        self.assertEqual(r["scenarios"][0]["unknown"], [1])

    def test_most_wins_tie_goes_to_ability_rank(self):
        horses = {1: h(0.5, 0.5), 2: h(0.5, 0.5)}
        r = step9_scenarios(horses, [2, 1])
        self.assertEqual(r["most_wins"], 2)


if __name__ == "__main__":
    unittest.main()
