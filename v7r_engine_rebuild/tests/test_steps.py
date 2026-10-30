# 架空データ（SYNTH）のみ。動作確認用であり、予想精度の確認ではない。
import unittest
from engine.models import PastResult, Horse, RaceCard
from engine.steps import (finish_score, step0_quality, step1_ability, step2_wpr,
                          step3_svi, step4_jockey, run_steps_0_to_4)


def past(finish, corners=(), field=18, venue="SYNTH", surface="芝", distance=2000, date="2099-01-01"):
    return PastResult(date=date, venue=venue, surface=surface, distance=distance,
                      finish=finish, corner_path=list(corners), field_size=field)


def card(horses, pace="ミドル", condition="良"):
    return RaceCard(race_id="SYNTH-1", date="2099-02-01", venue="SYNTH", surface="芝",
                    distance=2000, track_condition=condition, pace_label=pace, horses=horses)


class Step1(unittest.TestCase):
    def test_finish_score_bounds(self):
        self.assertEqual(finish_score(1), 1.0)
        self.assertEqual(finish_score(18), 0.0)
        self.assertIsNone(finish_score(None))

    def test_weighted_average_all_runs(self):
        h = Horse(1, "架空", past=[past(1), past(18), past(18)])
        r = step1_ability(h)
        self.assertAlmostEqual(r["ability_score"], 0.5 * 1.0 + 0.3 * 0 + 0.2 * 0, places=4)

    def test_missing_run_renormalizes_weights(self):
        h = Horse(1, "架空", past=[past(None), past(1)])
        self.assertAlmostEqual(step1_ability(h)["ability_score"], 1.0)

    def test_no_runs_gives_none_not_zero(self):
        self.assertIsNone(step1_ability(Horse(1, "架空"))["ability_score"])


class Step2(unittest.TestCase):
    def test_ideal_range_from_top3_and_tolerance(self):
        h = Horse(1, "架空", past=[past(2, [5]), past(3, [7]), past(12, [1])])
        r = step2_wpr(h)
        self.assertEqual(r["ideal_range"], (5, 7))
        self.assertEqual(r["allowed_range"], (3, 9))

    def test_fallback_to_top5_when_no_top3(self):
        h = Horse(1, "架空", past=[past(5, [4]), past(10, [9])])
        self.assertEqual(step2_wpr(h)["ideal_range"], (4, 4))

    def test_wpr_fraction_inside_allowed(self):
        h = Horse(1, "架空", past=[past(1, [5]), past(10, [1]), past(10, [12])])
        r = step2_wpr(h)
        self.assertAlmostEqual(r["wpr_score"], 1 / 3, places=4)

    def test_no_corner_data_is_none(self):
        self.assertIsNone(step2_wpr(Horse(1, "架空", past=[past(1)]))["wpr_score"])


class Step3(unittest.TestCase):
    def test_style_index_needs_field_size(self):
        h = Horse(1, "架空", past=[past(1, [1], field=None)])
        r = step3_svi(h, card([h], pace="ハイ"))
        self.assertIsNone(r["style_index"])
        self.assertIn("通過位置指数: 算出不能（通過順位または頭数が不足）", r["warnings"])

    def test_high_pace_benefit_is_style(self):
        h = Horse(1, "架空", past=[past(1, [19], field=19)])  # style_index = 1.0
        r = step3_svi(h, card([h], pace="ハイ"))
        self.assertEqual(r["pace_benefit"], 1.0)
        self.assertEqual(r["pace_damage"], 0.0)

    def test_slow_pace_benefit_is_inverse(self):
        h = Horse(1, "架空", past=[past(1, [1], field=19)])  # style_index = 0.0
        r = step3_svi(h, card([h], pace="スロー"))
        self.assertEqual(r["pace_benefit"], 1.0)

    def test_middle_pace_uses_rule_value_not_fill(self):
        h = Horse(1, "架空", past=[past(1, [10], field=19)])
        r = step3_svi(h, card([h], pace="ミドル"))
        self.assertEqual(r["pace_benefit"], 0.5)
        self.assertEqual(r["pace_damage"], 0.5)

    def test_unknown_pace_is_none_with_warning(self):
        h = Horse(1, "架空", past=[past(1, [10], field=19)])
        r = step3_svi(h, card([h], pace=None))
        self.assertIsNone(r["pace_benefit"])
        self.assertTrue(any("未入力" in w for w in r["warnings"]))

    def test_svi_does_not_overwrite_ability(self):
        h = Horse(1, "架空", past=[past(1, [10], field=19)])
        out = run_steps_0_to_4(card([h]))["horses"][1]
        self.assertIn("ability_score", out["step1"])
        self.assertIn("overall_svi", out["step3"])


class Step4(unittest.TestCase):
    def test_metrics_passed_through_unchanged(self):
        h = Horse(1, "架空", jockey="架空騎手", jockey_metrics={"course_fit": 0.7})
        r = step4_jockey(h)
        self.assertEqual(r["course_fit"], 0.7)
        self.assertIsNone(r["timing_reproducibility"])
        self.assertTrue(any("timing_reproducibility" in w for w in r["warnings"]))


class Step0(unittest.TestCase):
    def test_reports_gaps_without_filling(self):
        h = Horse(1, "架空", past=[past(None, [], field=None)])
        w = step0_quality(card([h], pace=None, condition=None))
        self.assertIn("馬場: 不明（推測で補わない）", w)
        self.assertIn("馬1: 騎手 不明", w)
        self.assertIn("馬1: 過去走 2099-01-01 の着順 不明", w)
        self.assertIn("馬1: 過去走 2099-01-01 の頭数 不明（H-4）", w)
        self.assertEqual(h.jockey, None)  # 補完されていない


if __name__ == "__main__":
    unittest.main()


class FieldSizeCheck(unittest.TestCase):
    def test_finish_beyond_field_size_is_contradiction(self):
        h = Horse(1, "架空", past=[past(12, [5], field=10)])
        w = step0_quality(card([h]))
        self.assertTrue(any(x.startswith("矛盾") and "着順 12 が頭数 10 を超えている" in x for x in w))

    def test_field_size_over_max_is_contradiction(self):
        h = Horse(1, "架空", past=[past(1, [1], field=19)])
        w = step0_quality(card([h]))
        self.assertTrue(any("範囲外" in x for x in w))

    def test_valid_field_size_has_no_contradiction(self):
        h = Horse(1, "架空", past=[past(3, [3], field=8)])
        w = step0_quality(card([h]))
        self.assertFalse(any(x.startswith("矛盾") for x in w))
