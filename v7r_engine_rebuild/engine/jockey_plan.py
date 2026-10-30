"""騎手の勝たせ方（戦術案）。判断は入れず、既存の結果と入力を並べる（仮）。

- 狙う番手: STEP2 の許容位置（理想位置 ± 2）。無ければ「不明」。
- ペース適合: 馬の理想ペース（STEP5）と当日の想定ペースが一致するか。
- 騎手指標: STEP4 の入力をそのまま使う。無い指標は「不明」。
- 騎手の実行可能性は、再現性（WPR）とは別項目として出す（設計文書の残課題に従う）。
- 有名騎手などの補正は入れない。
"""
from typing import Dict, Optional

JOCKEY_LABELS = {
    "positioning_reproducibility": "位置取りの再現性",
    "timing_reproducibility": "仕掛けの再現性",
    "course_fit": "コース適性（騎手）",
    "horse_fit": "馬との相性",
    "tactical_flexibility": "戦術の柔軟性",
}


def jockey_plan(horse_name: str, step2: Dict, step5_ideal_pace: Optional[str],
                card_pace: Optional[str], step4: Dict) -> Dict:
    rng = step2.get("allowed_range")
    aim = f"{rng[0]}〜{rng[1]}番手で進める" if rng else "不明（番手の範囲が算出できない）"
    if step5_ideal_pace is None or card_pace is None:
        fit = "不明（理想ペースまたは想定ペースが無い）"
    elif step5_ideal_pace == card_pace:
        fit = f"想定ペース（{card_pace}）と理想ペースが一致"
    else:
        fit = f"想定ペース（{card_pace}）と理想ペース（{step5_ideal_pace}）がずれる。騎手が位置を調整する必要あり"
    metrics = {JOCKEY_LABELS[k]: (step4.get(k) if step4.get(k) is not None else "不明")
               for k in JOCKEY_LABELS}
    return {
        "horse": horse_name,
        "aim_position": aim,
        "pace_fit": fit,
        "jockey_metrics": metrics,
        "reproducibility_note": "騎手の実行可能性は、WPR（再現性）とは別項目",
        "note": "戦術案（仮）。仕掛けの判断は含まない",
    }
