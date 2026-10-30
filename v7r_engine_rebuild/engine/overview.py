"""表示用の総合値（順位・判断には使わない）。

- 重みは全項目を同じ（1）とする。仮の値であり、競馬的な根拠はない。
- 欠けている項目は除外し、何項目で計算したかを必ず併記する（補完しない）。
- 馬場適正は、過去走の馬場状態が入っている走だけで計算する。気性は入力が無いため「不明」。
- 走り方の幅は WPR の一致率で代用する（仮定）。
"""
from typing import Dict
from . import thresholds as T  # noqa: F401  (閾値の集約先)

DISPLAY_WEIGHTS = {
    "能力(スタミナ・スピード)": 1.0,
    "距離適性": 1.0,
    "馬場適正": 1.0,
    "コース適性": 1.0,
    "走り方の幅": 1.0,
    "気性": 1.0,
}


def overview(step_results: Dict) -> Dict:
    """step_results: run_steps_0_to_4 の 1 頭分（horses[番号]）を受け取る。"""
    comps = {
        "能力(スタミナ・スピード)": step_results["step1"]["ability_score"],
        "距離適性": step_results["step3"]["distance_fit"],
        "馬場適正": step_results["step3"]["track_fit"],
        "コース適性": step_results["step3"]["course_fit"],
        "走り方の幅": step_results["step2"]["wpr_score"],  # 仮定: WPR で代用
        "気性": None,       # 入力なし
    }
    used = {k: v for k, v in comps.items() if v is not None}
    missing = [k for k, v in comps.items() if v is None]
    if used:
        total_w = sum(DISPLAY_WEIGHTS[k] for k in used)
        score = round(sum(v * DISPLAY_WEIGHTS[k] for k, v in used.items()) / total_w, 4)
    else:
        score = None
    return {"display_score": score, "used_count": len(used), "total_count": len(comps),
            "missing": missing, "note": "表示用。順位・判断には使わない"}
