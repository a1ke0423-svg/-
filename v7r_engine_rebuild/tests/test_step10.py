# 架空データのみ。着順確率の動作確認。
import unittest
from engine.step9 import step9_scenarios
from engine.step10 import step10_probabilities


def h(a, idx, wpr=0.5):
    return {"step1": {"ability_score": a}, "step2": {"wpr_score": wpr}, "step3": {"style_index": idx}}


class Prob(unittest.TestCase):
    def test_probabilities_sum_to_one_per_position_over_horses(self):
        horses = {1: h(0.8, 0.3), 2: h(0.7, 0.6), 3: h(0.6, 0.5)}
        s9 = step9_scenarios(horses, [1, 2, 3])
        r = step10_probabilities(s9, horses)
        for pos in (1, 2, 3):
            total = sum(r["horses"][n]["position_counts"].get(pos, 0) for n in horses)
            self.assertEqual(total, 9)

    def test_win_prob_matches_scenario_wins(self):
        horses = {1: h(0.9, 0.5), 2: h(0.1, 0.5)}
        s9 = step9_scenarios(horses, [1, 2])
        r = step10_probabilities(s9, horses)
        self.assertEqual(r["horses"][1]["win_prob"], round(s9["win_counts"][1] / 9, 4))

    def test_unknown_horse_gets_no_probability(self):
        horses = {1: h(None, 0.5), 2: h(0.5, 0.5)}
        s9 = step9_scenarios(horses, [2, 1])
        r = step10_probabilities(s9, horses)
        self.assertIsNone(r["horses"][1]["win_prob"])
        self.assertEqual(r["horses"][1]["unknown_scenarios"], 9)

    def test_reproducibility_kept_separate(self):
        horses = {1: h(0.8, 0.5, wpr=0.3)}
        s9 = step9_scenarios(horses, [1])
        r = step10_probabilities(s9, horses)
        self.assertEqual(r["horses"][1]["reproducibility_wpr"], 0.3)
        self.assertNotIn("reproducibility_wpr", {"win_prob"})


if __name__ == "__main__":
    unittest.main()
