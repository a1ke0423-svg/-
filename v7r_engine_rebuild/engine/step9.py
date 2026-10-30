"""STEP9 9シナリオ（仮。3×3 の枠組みは私の提案。docs/step9.md 参照）。

- 枠: 想定ペース（ハイ・ミドル・スロー）× 展開の決まり方（前残り・中間・差し有利）= 9 通り
- 各シナリオの馬の得点 = 能力 + 0.2 × (ペース恩恵 − 0.5) + 0.2 × (展開の決まり方の補正)
  - ペース恩恵: ハイ=通過位置指数、スロー=1−通過位置指数、ミドル=0.5（SVI と同じ考え）
  - 展開の補正: 前残り=(0.5−指数)、中間=0、差し有利=(指数−0.5)
- ランダム・乱数は使わない（同じ入力なら必ず同じ結果）。
- 能力または通過位置指数が無い馬は、そのシナリオでは順位の最後に並べ、「不明」と記録する。
- 最多勝馬: 9 シナリオで 1 着になった回数が最も多い馬。同数なら能力順位の高い方。
"""
from typing import Dict, List
from .step78 import step7_ability_rank

PACES = ["ハイ", "ミドル", "スロー"]
OUTCOMES = ["前残り", "中間", "差し有利"]
W_PACE = 0.2   # 仮
W_STYLE = 0.2  # 仮


def _benefit(pace, idx):
    if pace == "ハイ":
        return idx
    if pace == "スロー":
        return 1 - idx
    return 0.5


def _outcome_adj(outcome, idx):
    if outcome == "前残り":
        return 0.5 - idx
    if outcome == "差し有利":
        return idx - 0.5
    return 0.0


def step9_scenarios(horses: Dict[int, Dict], ability_order: List[int]) -> Dict:
    scenarios = []
    wins = {n: 0 for n in horses}
    rank_pos = {n: i for i, n in enumerate(ability_order)}
    for pace in PACES:
        for outcome in OUTCOMES:
            scores = {}
            unknown = []
            for n, r in horses.items():
                a = r["step1"]["ability_score"]
                idx = r["step3"]["style_index"]
                if a is None or idx is None:
                    unknown.append(n)
                    continue
                scores[n] = a + W_PACE * (_benefit(pace, idx) - 0.5) + W_STYLE * _outcome_adj(outcome, idx)
            order = sorted(scores, key=lambda n: (-scores[n], rank_pos.get(n, 10**6), n))
            order += sorted(unknown)
            winner = order[0] if order else None
            if winner is not None and winner in scores:
                wins[winner] += 1
            scenarios.append({"pace": pace, "outcome": outcome, "order": order,
                              "winner": winner, "unknown": sorted(unknown)})
    best = max(wins.values()) if wins else 0
    cands = [n for n, w in wins.items() if w == best and best > 0]
    most = min(cands, key=lambda n: rank_pos.get(n, 10**6)) if cands else None
    return {"scenarios": scenarios, "win_counts": wins, "most_wins": most,
            "note": "仮の枠組み。順位・判断は STEP13 で確定"}
