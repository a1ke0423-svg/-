"""netkeiba の競走成績ページ（db.netkeiba.com/horse/result/<ID>/）から
過去走の表を読み取り、AI 下書きの JSON を作る。

- 標準ライブラリのみ（追加インストール不要）。
- 取得できない項目は必ず "不明"。推測で埋めない。
- 出力は「下書き」。confirmed_by は null のまま。人が確認してから確定する。
- 実行は利用者の PC など、ネットに接続できる環境で行う。
- 取得間隔を空け（既定 2 秒）、取得した HTML は raw/ に保存する。

使い方:
  python3 tools/netkeiba_past_runs.py --ids 2022105102,2020100680 --out data/past_runs_draft.json
"""
import argparse
import datetime
import json
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

RESULT_URL = "https://db.netkeiba.com/horse/result/{hid}/"
UNKNOWN = "不明"
USER_AGENT = "Mozilla/5.0 (research; personal analysis; contact: owner)"


class _TableParser(HTMLParser):
    """class に db_h_race_results を持つ table の行と各セルのテキストを集める。"""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.depth = 0
        self.in_cell = False
        self.cell_buf = []
        self.row = []
        self.rows = []
        self.table_hits = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and "db_h_race_results" in (a.get("class") or ""):
            self.in_table = True
            self.depth = 0
            self.table_hits += 1
        if not self.in_table:
            return
        if tag == "table":
            self.depth += 1
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.cell_buf = []

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ("td", "th") and self.in_cell:
            self.row.append(" ".join("".join(self.cell_buf).split()))
            self.in_cell = False
        elif tag == "tr" and self.row:
            self.rows.append(self.row)
        elif tag == "table":
            self.depth -= 1
            if self.depth <= 0:
                self.in_table = False

    def handle_data(self, data):
        if self.in_cell:
            self.cell_buf.append(data)


def parse_result_html(html):
    """成績表を行のリストにする。ヘッダー名で列を引くので列順の変化に強い。"""
    p = _TableParser()
    p.feed(html)
    if not p.rows:
        return []
    header = p.rows[0]
    out = []
    for cells in p.rows[1:]:
        if len(cells) < len(header):
            continue
        out.append(dict(zip(header, cells)))
    return out


def _col(d, *names):
    for n in names:
        if n in d and d[n] != "":
            return d[n]
    return UNKNOWN


def normalize_row(d):
    """1走分を正規化する。値がなければ「不明」。"""
    surf_dist = _col(d, "距離")  # 例: "芝2000" "ダ1800"
    m = re.match(r"^(芝|ダ|障)\s*(\d{3,4})$", surf_dist)
    surface = m.group(1) if m else UNKNOWN
    distance = f"{m.group(2)}m" if m else UNKNOWN
    venue = re.sub(r"[\d回日]", "", _col(d, "開催")).strip() or UNKNOWN
    return {
        "date": _col(d, "日付"),
        "venue": venue,
        "race": _col(d, "レース名"),
        "surface": surface,
        "distance": distance,
        "track_condition": _col(d, "馬場"),
        "field_size": _col(d, "頭数"),
        "finish": _col(d, "着順"),
        "corner_path": _col(d, "通過"),
        "last_3f": _col(d, "上り", "上がり"),
    }


def fetch(hid, cache_dir, sleep_sec):
    url = RESULT_URL.format(hid=hid)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    html = raw.decode("euc-jp", errors="replace")
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, f"{hid}.html"), "w", encoding="utf-8") as f:
            f.write(html)
    time.sleep(sleep_sec)
    return url, html


def build_draft(hid, url, html, retrieved_at):
    rows = parse_result_html(html)
    runs = [normalize_row(r) for r in rows][:5]
    return {
        "horse_id": hid,
        "source_url": url,
        "retrieved_at": retrieved_at,
        "drafted_by": "AI(script)",
        "confirmed_by": None,
        "table_found": bool(rows),
        "runs": runs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True, help="netkeiba の馬ID（カンマ区切り）")
    ap.add_argument("--out", required=True, help="出力 JSON のパス")
    ap.add_argument("--raw-dir", default=None, help="取得した HTML の保存先")
    ap.add_argument("--sleep", type=float, default=2.0)
    args = ap.parse_args()

    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
    drafts, failed = [], []
    for hid in ids:
        try:
            url, html = fetch(hid, args.raw_dir, args.sleep)
            drafts.append(build_draft(hid, url, html, now))
        except Exception as e:  # 取得失敗は記録して次へ
            failed.append({"horse_id": hid, "error": str(e)})
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"drafts": drafts, "failed": failed}, f, ensure_ascii=False, indent=2)
    print(f"取得成功 {len(drafts)} 件 / 失敗 {len(failed)} 件 → {args.out}")


if __name__ == "__main__":
    main()
