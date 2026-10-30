import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netkeiba_past_runs import build_draft, normalize_row, parse_result_html  # noqa: E402

# 合成データ（実サイトの取得結果ではない）
SAMPLE = """
<table class="db_h_race_results"><tr>
<th>日付</th><th>開催</th><th>レース名</th><th>距離</th><th>馬場</th><th>頭数</th><th>着順</th><th>通過</th><th>上がり</th>
</tr><tr>
<td>2026/06/14</td><td>2阪神8</td><td>宝塚記念(GI)</td><td>芝2200</td><td>重</td><td>18</td><td>2</td><td>5-5-4-3</td><td>35.2</td>
</tr><tr>
<td>2026/04/26</td><td>海外</td><td>QE2世C(GI)</td><td>芝2000</td><td>良</td><td></td><td>5</td><td></td><td></td>
</tr></table>
"""


class ParseTests(unittest.TestCase):
    def test_parses_rows_by_header(self):
        rows = parse_result_html(SAMPLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["レース名"], "宝塚記念(GI)")

    def test_normalize_known_values(self):
        r = normalize_row(parse_result_html(SAMPLE)[0])
        self.assertEqual(r["surface"], "芝")
        self.assertEqual(r["distance"], "2200m")
        self.assertEqual(r["venue"], "阪神")
        self.assertEqual(r["finish"], "2")
        self.assertEqual(r["corner_path"], "5-5-4-3")

    def test_empty_cells_become_unknown(self):
        r = normalize_row(parse_result_html(SAMPLE)[1])
        self.assertEqual(r["field_size"], "不明")
        self.assertEqual(r["corner_path"], "不明")
        self.assertEqual(r["last_3f"], "不明")

    def test_no_table_gives_empty_draft(self):
        d = build_draft("1", "u", "<html></html>", "t")
        self.assertFalse(d["table_found"])
        self.assertEqual(d["runs"], [])
        self.assertIsNone(d["confirmed_by"])
        self.assertEqual(d["drafted_by"], "AI(script)")


if __name__ == "__main__":
    unittest.main()
