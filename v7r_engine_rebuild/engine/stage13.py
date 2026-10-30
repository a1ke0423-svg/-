"""STEP13 予測固定（記録・検証の仕組みに接続）。

- 固定の前に、STEP0〜12 を順に実行する。
- STEP6 が blocked、または STEP11 が fail の場合は固定しない。
- 最終全着順（仮の決め方・私の提案）: 1着確率の高い順 → 3着内確率の高い順 → 能力順位 → 馬番。
- 比較用の予測: 「V7R」= 最終全着順、「ベースライン」= 能力順位、「見立て」= あなたの予想（入力）。
- 記録は v7r_records/ledger.py の Ledger.fix() に渡す（追記のみ・1レース1回）。
"""
import os
import sys
from typing import Dict, List

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "v7r_records"))
from ledger import Ledger, LedgerError  # noqa: E402

from .models import Horse, PastResult, RaceCard  # noqa: E402
from .steps import run_steps_0_to_4  # noqa: E402
from .step5 import step5_routes  # noqa: E402
from .step6 import step6_redteam  # noqa: E402
from .step78 import step7_ability_rank, step8_wpr_rank  # noqa: E402
from .step9 import step9_scenarios  # noqa: E402
from .step10 import step10_probabilities  # noqa: E402
from .blue_team import audit, audit_inputs, summary  # noqa: E402
from .strategy import strategy_summary  # noqa: E402
from .overview import overview  # noqa: E402


def _to_card(raw: Dict) -> RaceCard:
    tc = raw.get("track_condition")
    horses = []
    for h in raw["horses"]:
        past = []
        for p in h.get("past", []):
            past.append(PastResult(
                date=p["date"], venue=p["venue"], surface=p["surface"], distance=p["distance"],
                finish=p.get("finish"), corner_path=p.get("corner_path", []),
                field_size=p.get("field_size"),
                track_condition=(None if p.get("track_condition") in (None, "不明") else p["track_condition"])))
        horses.append(Horse(number=h["number"], name=h["name"], weight=h.get("weight"),
                            past=past, jockey=h.get("jockey"),
                            jockey_metrics=h.get("jockey_metrics")))
    return RaceCard(race_id=raw["race_id"], date=raw["date"], venue=raw["venue"],
                    surface=raw["surface"], distance=raw["distance"],
                    track_condition=(None if tc in (None, "不明") else tc),
                    pace_label=raw.get("pace_label"), horses=horses)


def run_all(raw: Dict) -> Dict:
    card = _to_card(raw)
    step = run_steps_0_to_4(card)
    horses = step["horses"]
    step5 = step5_routes(horses)
    redteam_input_horses = horses
    redteam = step6_redteam(card.pace_label, redteam_input_horses, step5,
                            unknown_sources={n: [] for n in horses})
    step7 = step7_ability_rank(horses, redteam)
    step8 = step8_wpr_rank(horses)
    step9 = step9_scenarios(horses, step7["order"])
    step10 = step10_probabilities(step9, horses)
    overview_missing = {n: overview(horses[n])["missing"] for n in horses}
    blue_items = audit_inputs(raw) + audit(horses, step5, redteam, step7, step9, step10, overview_missing)
    blue = summary(blue_items)
    strat = strategy_summary(horses, step7, step9, step10, redteam, blue)

    rank_pos = {n: i for i, n in enumerate(step7["order"])}
    def key(n):
        wp = step10["horses"][n]["win_prob"]
        t3 = step10["horses"][n]["top3_prob"]
        return (wp is None, -(wp or 0), -(t3 or 0), rank_pos.get(n, 10**6), n)
    final_order = sorted(horses, key=key)
    return {"step": step, "step5": step5, "redteam": redteam, "step7": step7, "step8": step8,
            "step9": step9, "step10": step10, "blue_items": blue_items, "blue": blue,
            "strategy": strat, "final_order": final_order, "card": raw}


def fix_race(ledger_path: str, raw: Dict, human_order: List[int], fixed_by: str) -> Dict:
    res = run_all(raw)
    if res["redteam"]["status"] == "blocked":
        raise LedgerError(f"固定しません（STEP6 blocked: {res['redteam']['reason']}）")
    if res["blue"].startswith("fail"):
        raise LedgerError("固定しません（STEP11 fail。工程を直してから固定する）")
    predictions = {
        "v7r": res["final_order"],
        "human": list(human_order),
        "baseline": res["step7"]["order"],
    }
    rec = Ledger(ledger_path).fix(raw, predictions, fixed_by=fixed_by)
    return {"record": rec, "blue": res["blue"], "final_order": res["final_order"]}
