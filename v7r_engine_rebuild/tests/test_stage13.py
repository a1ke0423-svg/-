# 架空データのみ（SYNTH）。STEP13 の固定と台帳への記録を確認する。
import os, tempfile, unittest
from engine.stage13 import run_all, fix_race
from ledger import LedgerError, Ledger


def past(date, finish, corners, field=10, surface="芝", venue="SYNTH", cond="良", dist=2000):
    return {"date": date, "venue": venue, "surface": surface, "distance": dist, "finish": finish,
            "corner_path": corners, "field_size": field, "track_condition": cond}


def raw_card(rid="SYNTH-STAGE13-1", n=4):
    horses = []
    for i in range(1, n + 1):
        horses.append({"number": i, "name": f"架空馬{i}", "jockey": f"架空騎手{i}", "frame": i,
                       "past": [past("2099-01-01", i, [i], field=10),
                                past("2098-01-01", i + 1, [i + 1], field=10)],
                       "jockey_metrics": {"course_fit": 0.6}})
    return {"race_id": rid, "date": "2099-02-01", "venue": "SYNTH", "race_no": 1,
            "distance": 2000, "surface": "芝", "course": "芝", "track_condition": "良",
            "pace_label": "ミドル", "horses": horses}


class Stage13(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "records.jsonl")

    def test_run_all_produces_full_order(self):
        res = run_all(raw_card())
        self.assertEqual(sorted(res["final_order"]), [1, 2, 3, 4])
        self.assertIn(res["blue"].split("（")[0], ("pass", "review", "fail"))

    def test_fix_writes_record_with_three_sources(self):
        out = fix_race(self.path, raw_card(), human_order=[4, 3, 2, 1], fixed_by="テスト担当")
        rec = out["record"]
        self.assertEqual(rec["kind"], "fix")
        self.assertEqual(set(rec["payload"]["predictions"]), {"v7r", "human", "baseline"})
        self.assertEqual(Ledger(self.path).verify(), 1)

    def test_second_fix_of_same_race_refused(self):
        fix_race(self.path, raw_card(), human_order=[1, 2, 3, 4], fixed_by="テスト担当")
        with self.assertRaises(LedgerError):
            fix_race(self.path, raw_card(), human_order=[1, 2, 3, 4], fixed_by="テスト担当")

    def test_human_order_must_be_full(self):
        with self.assertRaises(LedgerError):
            fix_race(self.path, raw_card(), human_order=[1, 2, 3], fixed_by="テスト担当")

    def test_market_key_in_input_blocks_via_blue_team(self):
        raw = raw_card(rid="SYNTH-STAGE13-2")
        raw["odds"] = 2.5
        res = run_all(raw)
        self.assertTrue(res["blue"].startswith("fail"))
        with self.assertRaises(LedgerError):
            fix_race(self.path, raw, human_order=[1, 2, 3, 4], fixed_by="テスト担当")


if __name__ == "__main__":
    unittest.main()
