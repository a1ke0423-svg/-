# 注意: すべて架空データ（SYNTH）。実レースの検証には使わない。
import json, os, tempfile, unittest
from ledger import Ledger, LedgerError, compare, validate_card


def card(rid="SYNTH-0001", n=4, condition="良"):
    return {
        "race_id": rid, "date": "2099-01-01", "venue": "SYNTH", "race_no": 1,
        "distance": 2000, "course": "芝", "track_condition": condition,
        "horses": [{"number": i, "name": f"架空馬{i}", "jockey": f"架空騎手{i}", "frame": i}
                   for i in range(1, n + 1)],
    }


def preds(nums=(1, 2, 3, 4)):
    o = list(nums)
    return {"v7r": o, "human": list(reversed(o)), "baseline": o[1:] + o[:1]}


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "records.jsonl")
        self.led = Ledger(self.path)

    def register(self, rid="SYNTH-0001", order=(1, 2, 3, 4), **kw):
        args = dict(status="confirmed", source_url="https://example.invalid/synth",
                    retrieved_at="2099-01-01T12:00:00+09:00", drafted_by="AI",
                    confirmed_by="テスト担当", reason="")
        args.update(kw)
        return self.led.register_result(rid, list(order), **args)

    # 形式チェック
    def test_card_ok(self):
        self.assertEqual(validate_card(card()), [1, 2, 3, 4])

    def test_card_rejects_unknown_track_condition(self):
        with self.assertRaises(LedgerError):
            validate_card(card(condition="晴"))

    def test_card_allows_unknown_track_condition_marked_unknown(self):
        self.assertEqual(validate_card(card(condition="不明"))[0], 1)

    def test_card_rejects_empty_field(self):
        c = card(); c["horses"][0]["jockey"] = ""
        with self.assertRaises(LedgerError):
            validate_card(c)

    def test_card_rejects_duplicate_number(self):
        c = card(); c["horses"][1]["number"] = 1
        with self.assertRaises(LedgerError):
            validate_card(c)

    # 固定
    def test_fix_then_append(self):
        r = self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.assertEqual(r["seq"], 1)
        self.assertEqual(self.led.verify(), 1)

    def test_fix_rejects_second_fix_same_race(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        with self.assertRaises(LedgerError):
            self.led.fix(card(), preds(), fixed_by="テスト担当")

    def test_fix_rejects_incomplete_prediction(self):
        p = preds(); p["human"] = [1, 2, 3]
        with self.assertRaises(LedgerError):
            self.led.fix(card(), p, fixed_by="テスト担当")

    def test_fix_rejects_missing_source(self):
        p = preds(); del p["baseline"]
        with self.assertRaises(LedgerError):
            self.led.fix(card(), p, fixed_by="テスト担当")

    def test_fix_requires_fixed_by(self):
        with self.assertRaises(LedgerError):
            self.led.fix(card(), preds(), fixed_by="")

    # 結果
    def test_result_requires_fix_first(self):
        with self.assertRaises(LedgerError):
            self.register()

    def test_result_after_fix(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.register()
        self.assertEqual(self.led.verify(), 2)

    def test_result_requires_full_order(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        with self.assertRaises(LedgerError):
            self.register(order=(1, 2, 3))

    def test_result_requires_source_and_both_people(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        with self.assertRaises(LedgerError):
            self.register(source_url="")
        with self.assertRaises(LedgerError):
            self.register(drafted_by="")
        with self.assertRaises(LedgerError):
            self.register(confirmed_by="")

    def test_confirmed_result_cannot_be_overwritten_without_correction(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.register()
        with self.assertRaises(LedgerError):
            self.register(order=(4, 3, 2, 1))

    def test_correction_needs_reason(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.register()
        with self.assertRaises(LedgerError):
            self.register(order=(4, 3, 2, 1), status="corrected")
        self.register(order=(4, 3, 2, 1), status="corrected", reason="公式訂正")
        self.assertEqual(self.led.verify(), 3)

    # 改ざん検出
    def test_verify_detects_edited_line(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        with open(self.path, encoding="utf-8") as f:
            line = f.read()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(line.replace("架空馬1", "架空馬X"))
        with self.assertRaises(LedgerError):
            self.led.verify()

    def test_verify_detects_deleted_line(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.register()
        with open(self.path, encoding="utf-8") as f:
            lines = f.readlines()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(lines[1])
        with self.assertRaises(LedgerError):
            self.led.verify()

    # 比較
    def test_compare_counts_only_races_with_result(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.led.fix(card("SYNTH-0002"), preds(), fixed_by="テスト担当")
        self.register()
        s = compare(self.path)
        self.assertEqual(s["v7r"]["races"], 1)
        self.assertEqual(s["v7r"]["top1_hits"], 1)
        self.assertEqual(s["human"]["top1_hits"], 0)

    def test_compare_values(self):
        self.led.fix(card(), preds(), fixed_by="テスト担当")
        self.register(order=(1, 2, 3, 4))
        s = compare(self.path)
        self.assertEqual(s["v7r"]["mean_abs_rank_error"], 0.0)
        self.assertGreater(s["human"]["mean_abs_rank_error"], 0.0)


if __name__ == "__main__":
    unittest.main()
