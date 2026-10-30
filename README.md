# a.11-uma.syumire（V7R 記録・検証）

- 対象: JRA の実レースのみ（地方は対象外）
- 予測ロジック（V7R Ver.8）は含まない。ここでは、固定・結果登録・比較の記録だけを扱う。
- テストは架空データ（SYNTH）で行う。実レースの検証には使わない。

## 実行
- テスト: `cd v7r_records && python3 -m unittest tests.test_ledger`
- 日次チェック: `cd v7r_records && python3 daily_check.py <台帳ファイル>`

## 方針
- 予測は結果より前に固定する。固定後の変更は拒否する。
- 結果は、AI が下書きし、人が公式情報と照らして確認してから登録する。
- 予測の中身の見直しは、30レースたまってから人が判断する。

## netkeiba 過去走の取得（下書き作成）
- 実行: `python3 tools/netkeiba_past_runs.py --ids <馬ID,馬ID,...> --out data/<名前>.json --raw-dir data/raw`
- 出力は「下書き」（confirmed_by は null）。人が確認してから確定する。
- 取得できない項目は「不明」。ページ構造が変わると解析が止まるので、テストで確認する。
- テスト: `cd tools && python3 -m unittest tests.test_netkeiba_past_runs`
- 実サイトでの動作は未確認（作成環境から netkeiba に接続できないため）。最初の実行は少数の馬で試す。
