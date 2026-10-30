"""STEP7 能力順位 / STEP8 WPR順位（並べ替えのみ。新しい判断は入れない）。

- 能力順位: 能力スコア降順。同点は馬番の小さい方。
- WPR順位: WPR 降順。同点は馬番の小さい方。
- 値が無い馬（None）は順位を付けず、最後に「不明」として並べる。
- STEP6 の能力首位の暫定監査は、STEP7 で確定する。ただし順位は変えない（降格は記録のみ）。
"""
from typing import Dict, List


def _rank(values: Dict[int, object], key_name: str) -> Dict:
    known = [(n, v) for n, v in values.items() if v is not None]
    unknown = sorted(n for n, v in values.items() if v is None)
    known.sort(key=lambda t: (-t[1], t[0]))
    order = [n for n, _ in known] + unknown
    ranks = {n: i + 1 for i, n in enumerate([n for n, _ in known])}
    for n in unknown:
        ranks[n] = None
    return {"order": order, "ranks": ranks, "unknown": unknown, "basis": key_name}


def step7_ability_rank(horses: Dict[int, Dict], redteam: Dict) -> Dict:
    values = {n: r["step1"]["ability_score"] for n, r in horses.items()}
    out = _rank(values, "能力スコア（降順。同点は馬番）")
    audit = redteam.get("horses", {}).get("top_ability_audit")
    out["top_audit"] = audit
    out["top_downgrade_note"] = (
        "降格の記録のみ。順位は変更しない" if audit else "監査なし")
    return out


def step8_wpr_rank(horses: Dict[int, Dict]) -> Dict:
    values = {n: r["step2"]["wpr_score"] for n, r in horses.items()}
    return _rank(values, "WPR（降順。同点は馬番）")
