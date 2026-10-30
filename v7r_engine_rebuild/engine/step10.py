"""STEP10 着順確率（設計文書 0.1.0 の方針に従う）。

- 着順確率: 9 シナリオでその馬が各着順になった割合（回数 ÷ 9）。
- 再現性（WPR）は、着順確率と混ぜず、別項目として並べる（能力と再現性を分離）。
- 入力が無い馬（シナリオで「不明」）は、確率を出さず、不明の回数を記録する。
- 分母は常に 9（不明も数える）。
"""
from typing import Dict

N_SCENARIOS = 9


def step10_probabilities(step9: Dict, horses: Dict) -> Dict:
    scenarios = step9["scenarios"]
    total = len(scenarios)
    out = {}
    for n in horses:
        counts = {}
        unknown = 0
        for s in scenarios:
            if n in s["unknown"]:
                unknown += 1
                continue
            pos = s["order"].index(n) + 1
            counts[pos] = counts.get(pos, 0) + 1
        ranked = total - unknown
        out[n] = {
            "win_prob": round(counts.get(1, 0) / total, 4) if ranked else None,
            "top3_prob": round(sum(counts.get(k, 0) for k in (1, 2, 3)) / total, 4) if ranked else None,
            "position_counts": dict(sorted(counts.items())),
            "unknown_scenarios": unknown,
            "reproducibility_wpr": horses[n]["step2"]["wpr_score"],  # 能力とは別項目
        }
    return {"denominator": total, "horses": out, "note": "9 シナリオ由来の割合。再現性は別項目"}
