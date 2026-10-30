# 架空データのみ。並べ替えの動作確認。
import unittest
from engine.step78 import step7_ability_rank, step8_wpr_rank


def h(ability, wpr):
    return {"step1": {"ability_score": ability}, "step2": {"wpr_score": wpr}}


class Rank(unittest.TestCase):
    def test_ability_order_desc_and_tie_by_number(self):
        horses = {3: h(0.7, None), 1: h(0.9, None), 2: h(0.7, None)}
        r = step7_ability_rank(horses, {"horses": {}})
        self.assertEqual(r["order"], [1, 2, 3])
        self.assertEqual(r["ranks"][2], 2)
        self.assertEqual(r["ranks"][3], 3)

    def test_none_ranked_last_with_no_rank(self):
        horses = {1: h(None, None), 2: h(0.5, None)}
        r = step7_ability_rank(horses, {"horses": {}})
        self.assertEqual(r["order"], [2, 1])
        self.assertIsNone(r["ranks"][1])
        self.assertEqual(r["unknown"], [1])

    def test_wpr_rank(self):
        horses = {1: h(None, 0.4), 2: h(None, 0.8), 3: h(None, None)}
        r = step8_wpr_rank(horses)
        self.assertEqual(r["order"], [2, 1, 3])

    def test_downgrade_is_recorded_not_applied(self):
        horses = {1: h(0.9, None), 2: h(0.5, None)}
        audit = {"horse": 1, "slots": {}, "downgrade_eligible": False}
        r = step7_ability_rank(horses, {"horses": {"top_ability_audit": audit}})
        self.assertEqual(r["order"][0], 1)
        self.assertIn("順位は変更しない", r["top_downgrade_note"])


if __name__ == "__main__":
    unittest.main()
