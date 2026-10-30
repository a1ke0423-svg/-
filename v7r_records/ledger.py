"""V7R 記録・検証台帳（テスト用・予測の中身には触れない）

- 追記のみ（JSONL）。各行はハッシュ連鎖で前の行と結びつく。
- 固定（fix）は 1 レース 1 回だけ。結果（result）は固定の後にだけ登録できる。
- 固定後の入力・予測は変更できない（同じ race_id の再固定を拒否）。
- 結果は着順・出典 URL・取得時刻・下書き者・確認者を必須とする。
"""
import hashlib, json, os, datetime

TRACK_CONDITIONS = {"良", "稍重", "重", "不良", "不明"}
RESULT_STATUS = {"provisional", "confirmed", "corrected"}
SOURCES = ("v7r", "human", "baseline")


def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class LedgerError(Exception):
    pass


def validate_card(card):
    """出走表の形式チェック。欠落や矛盾があれば LedgerError。"""
    required = ["race_id", "date", "venue", "race_no", "distance", "course", "track_condition", "horses"]
    for k in required:
        if k not in card:
            raise LedgerError(f"出走表に項目がありません: {k}")
    if card["track_condition"] not in TRACK_CONDITIONS:
        raise LedgerError(f"馬場の値が不正です: {card['track_condition']}（良・稍重・重・不良・不明のいずれか）")
    horses = card["horses"]
    if not horses:
        raise LedgerError("出走馬がいません")
    nums = [h.get("number") for h in horses]
    if len(set(nums)) != len(nums):
        raise LedgerError("馬番が重複しています")
    for h in horses:
        for k in ["number", "name", "jockey", "frame"]:
            if h.get(k) in (None, ""):
                raise LedgerError(f"馬 {h.get('number')} の項目が空です: {k}（不明なら「不明」と入れる）")
    return sorted(nums)


def validate_order(order, horse_numbers, label):
    """予測や結果の全着順が、出走馬の並べ替えになっているかを確認。"""
    if sorted(order) != sorted(horse_numbers):
        raise LedgerError(f"{label} は全出走馬の並べ替えである必要があります")


class Ledger:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    def _rows(self):
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def _append(self, kind, race_id, payload, extra):
        rows = self._rows()
        prev = rows[-1]["hash"] if rows else "GENESIS"
        body = {
            "seq": len(rows) + 1,
            "kind": kind,
            "race_id": race_id,
            "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "payload": payload,
            **extra,
            "prev_hash": prev,
        }
        body["hash"] = _sha(_canon(body))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(_canon(body) + "\n")
        return body

    def fix(self, card, predictions, fixed_by):
        """発走前の予測固定。predictions は {"v7r": [...], "human": [...], "baseline": [...]} の全着順。"""
        numbers = validate_card(card)
        rid = card["race_id"]
        if any(r["kind"] == "fix" and r["race_id"] == rid for r in self._rows()):
            raise LedgerError(f"{rid} は固定済みです。固定後の変更は許可されていません")
        for src in SOURCES:
            if src not in predictions:
                raise LedgerError(f"予測が不足しています: {src}")
            validate_order(predictions[src], numbers, f"予測({src})")
        if not fixed_by:
            raise LedgerError("見立て担当者（fixed_by）が必要です")
        return self._append("fix", rid, {"card": card, "card_hash": _sha(_canon(card)),
                                         "predictions": predictions},
                            {"fixed_by": fixed_by})

    def register_result(self, race_id, order, status, source_url, retrieved_at,
                         drafted_by, confirmed_by, reason=""):
        """結果登録。固定が無いと拒否。確定済みの上書きは corrected と理由が必要。"""
        rows = self._rows()
        fix = [r for r in rows if r["kind"] == "fix" and r["race_id"] == race_id]
        if not fix:
            raise LedgerError(f"{race_id} の固定が無いため、結果を登録できません")
        if status not in RESULT_STATUS:
            raise LedgerError(f"結果の区分が不正です: {status}")
        prior = [r for r in rows if r["kind"] == "result" and r["race_id"] == race_id]
        if prior and status != "corrected":
            raise LedgerError(f"{race_id} の結果は登録済みです。訂正は status=corrected と理由が必要です")
        if prior and not reason:
            raise LedgerError("訂正には理由が必要です")
        if not source_url or not retrieved_at:
            raise LedgerError("出典 URL と取得時刻が必要です")
        if not drafted_by or not confirmed_by:
            raise LedgerError("下書き者と確認者の両方が必要です（AI 下書き・人確認）")
        numbers = [h["number"] for h in fix[0]["payload"]["card"]["horses"]]
        validate_order(order, numbers, "結果の着順")
        return self._append("result", race_id, {"order": order},
                            {"status": status, "source_url": source_url,
                             "retrieved_at": retrieved_at, "drafted_by": drafted_by,
                             "confirmed_by": confirmed_by, "reason": reason})

    def verify(self):
        """ハッシュ連鎖を検査。改ざん・削除があれば LedgerError。"""
        prev = "GENESIS"
        for i, row in enumerate(self._rows(), start=1):
            if row["seq"] != i:
                raise LedgerError(f"行 {i}: 連番が一致しません")
            if row["prev_hash"] != prev:
                raise LedgerError(f"行 {i}: 前の行とのつながりが壊れています")
            body = {k: v for k, v in row.items() if k != "hash"}
            if _sha(_canon(body)) != row["hash"]:
                raise LedgerError(f"行 {i}: 内容が変更されています")
            if row["kind"] == "fix" and row["payload"]["card_hash"] != _sha(_canon(row["payload"]["card"])):
                raise LedgerError(f"行 {i}: 出走表のハッシュが一致しません")
            prev = row["hash"]
        return len(self._rows())


def compare(ledger_path):
    """固定と結果がそろったレースについて、3 つの予測源を比較する。"""
    rows = Ledger(ledger_path)._rows()
    fixes = {r["race_id"]: r for r in rows if r["kind"] == "fix"}
    results = {}
    for r in rows:
        if r["kind"] == "result":
            results[r["race_id"]] = r  # 最後の結果を採用
    summary = {s: {"races": 0, "top1_hits": 0, "top3_overlap": 0, "mean_abs_rank_error": 0.0} for s in SOURCES}
    for rid, res in results.items():
        if rid not in fixes:
            continue
        actual = res["payload"]["order"]
        actual_rank = {n: i + 1 for i, n in enumerate(actual)}
        for s in SOURCES:
            pred = fixes[rid]["payload"]["predictions"][s]
            sm = summary[s]
            sm["races"] += 1
            sm["top1_hits"] += int(pred[0] == actual[0])
            sm["top3_overlap"] += len(set(pred[:3]) & set(actual[:3]))
            pred_rank = {n: i + 1 for i, n in enumerate(pred)}
            err = [abs(pred_rank[n] - actual_rank[n]) for n in actual]
            sm["mean_abs_rank_error"] += sum(err) / len(err)
    for s in SOURCES:
        n = summary[s]["races"]
        if n:
            summary[s]["mean_abs_rank_error"] = round(summary[s]["mean_abs_rank_error"] / n, 3)
    return summary
