"""STEP6 Red Team（設計文書 0.1.0）。

- 役割は監査。予測順位・能力・WPR・SVI・騎手評価は変更しない（読むだけ）。
- STEP5 が未完了（incomplete・ルート欠落・条件空）なら blocked。後続へ進めない。
- 反証の種類: accepted（成立）/ not_triggered（検査したが成立せず）/ unknown（根拠不足）。
- accepted は参照 STEP・項目・値・発生条件・影響対象・反証対象の主張を必ず持つ。
"""
from typing import Dict, List, Optional
from . import thresholds as T
from .step5 import ideal_pace

LOSS_CATEGORIES = ["pace_failure", "position_failure", "fit_failure", "jockey_execution_risk"]


def _cp(kind, category, claim, step_refs, items, values, trigger, affected, challenges):
    return {"kind": kind, "category": category, "claim": claim, "step_refs": step_refs,
            "items": items, "values": values, "trigger": trigger, "affected": affected,
            "challenges": challenges}


def _blocked_reason(step5: Dict, horses: Dict) -> Optional[str]:
    for num, rt in step5.items():
        if rt.get("status") != "complete":
            return f"馬{num}: STEP5 が incomplete"
        if not rt.get("wins") or not rt.get("losses"):
            return f"馬{num}: 勝利条件または敗北条件が空"
        if num not in horses:
            return f"馬{num}: STEP1〜4 の結果が無い"
    return None


def _check_horse(num, r, rt, card_pace, unknown_sources):
    s1, s2, s3, s4 = r["step1"], r["step2"], r["step3"], r["step4"]
    cps = []
    challenge = [c["text"] for c in rt["wins"] if c.get("met")] or ["勝利条件（根拠なし）"]
    style = s3["style_index"]
    wpr = s2["wpr_score"]

    # 展開崩壊
    pd = s3["pace_damage"]
    if pd is None:
        cps.append(_cp("unknown", "pace_failure", "展開で崩れる", ["STEP3"], ["pace_damage"],
                       {}, "展開被害の算出", "当該馬", challenge))
    elif pd >= T.PACE_DAMAGE_COLLAPSE:
        cps.append(_cp("accepted", "pace_failure", "展開で崩れる", ["STEP3"], ["pace_damage"],
                       {"pace_damage": pd}, "展開被害 ≥ 6.0", "当該馬", challenge))
    else:
        cps.append(_cp("not_triggered", "pace_failure", "展開で崩れる", ["STEP3"], ["pace_damage"],
                       {"pace_damage": pd}, "展開被害 ≥ 6.0（不成立）", "当該馬", challenge))

    # 位置取り失敗
    pos_hit = None
    if style is None or wpr is None or card_pace is None:
        cps.append(_cp("unknown", "position_failure", "位置を取れず崩れる", ["STEP2", "STEP3"],
                       ["style_index", "wpr_score", "想定ペース"], {}, "位置・想定ペースの算出", "当該馬", challenge))
    else:
        if (style < 0.35 and card_pace == "ハイ") or (style > 0.65 and card_pace == "スロー") or wpr < T.FIT_MIN:
            pos_hit = True
        cps.append(_cp("accepted" if pos_hit else "not_triggered", "position_failure",
                       "位置を取れず崩れる", ["STEP2", "STEP3"], ["style_index", "wpr_score", "想定ペース"],
                       {"style_index": style, "wpr_score": wpr, "想定ペース": card_pace},
                       "前寄り×ハイ / 後寄り×スロー / WPR < 5.0", "当該馬", challenge))

    # 適性不足（距離・コース・馬場）
    for key, label in [("distance_fit", "距離"), ("course_fit", "コース"), ("track_fit", "馬場")]:
        v = s3[key]
        if v is None:
            cps.append(_cp("unknown", "fit_failure", f"{label}適性不足（初条件の可能性）", ["STEP3"],
                           [key], {}, f"{label}適性の算出", "当該馬", challenge))
        elif v < T.FIT_MIN:
            cps.append(_cp("accepted", "fit_failure", f"{label}適性不足", ["STEP3"], [key],
                           {key: v}, f"{label}適性 < 5.0", "当該馬", challenge))
        else:
            cps.append(_cp("not_triggered", "fit_failure", f"{label}適性不足", ["STEP3"], [key],
                           {key: v}, f"{label}適性 < 5.0（不成立）", "当該馬", challenge))

    # 騎手実行リスク（騎手指標 < 0.50 かつ 不一致あり。当該馬との戦術不一致は入力が無いため未使用）
    jm = [s4[k] for k in ["positioning_reproducibility", "timing_reproducibility", "course_fit",
                          "horse_fit", "tactical_flexibility"] if s4.get(k) is not None]
    if not jm:
        cps.append(_cp("unknown", "jockey_execution_risk", "騎手の実行が崩れる", ["STEP4"],
                       ["騎手指標"], {}, "騎手指標の入力", "当該馬", challenge))
    else:
        low = min(jm) < T.FIT_MIN
        mismatch = (wpr is not None and wpr < T.FIT_MIN) or (
            ideal_pace(style) is not None and card_pace is not None and ideal_pace(style) != card_pace)
        hit = low and mismatch
        cps.append(_cp("accepted" if hit else "not_triggered", "jockey_execution_risk",
                       "騎手の実行が崩れる", ["STEP4", "STEP2", "STEP3"], ["騎手指標", "WPR", "想定展開"],
                       {"min_jockey": min(jm)}, "騎手指標 < 5.0 かつ 不一致あり", "当該馬", challenge))

    # 相手リスク
    if rt["key_opponents"]:
        cps.append(_cp("accepted", "opponent_risk", "能力が近い相手に負ける", ["STEP5"],
                       ["key_opponents"], {"opponents": rt["key_opponents"]},
                       "能力差 1.0 以内・理想位置が重なる", "当該馬", challenge))
    else:
        cps.append(_cp("not_triggered", "opponent_risk", "能力が近い相手に負ける", ["STEP5"],
                       ["key_opponents"], {"opponents": []}, "能力差 1.0 以内の重なり（該当なし）", "当該馬", challenge))

    # 矛盾
    s1v = s1["ability_score"]
    if s1v is not None and wpr is not None:
        if s1v >= T.CONTRADICTION_ABILITY and wpr < T.FIT_MIN:
            cps.append(_cp("accepted", "contradiction", "能力と位置取りが噛み合わない", ["STEP1", "STEP2"],
                           ["ability_score", "wpr_score"], {"ability": s1v, "wpr": wpr},
                           "能力 ≥ 8.0 かつ WPR < 5.0", "当該馬", challenge))
        else:
            cps.append(_cp("not_triggered", "contradiction", "能力と位置取りが噛み合わない", ["STEP1", "STEP2"],
                           ["ability_score", "wpr_score"], {"ability": s1v, "wpr": wpr},
                           "能力 ≥ 8.0 かつ WPR < 5.0（不成立）", "当該馬", challenge))

    # 未知リスク（STEP0・STEP3・STEP4 の警告）
    unknowns = list(unknown_sources.get(num, [])) + s3["warnings"] + s4["warnings"]
    return cps, unknowns


def step6_redteam(card_pace, horses: Dict, step5: Dict, unknown_sources: Dict) -> Dict:
    reason = _blocked_reason(step5, horses)
    if reason:
        return {"status": "blocked", "reason": reason, "horses": {}}

    result = {}
    for num, r in horses.items():
        cps, unknowns = _check_horse(num, r, step5[num], card_pace, unknown_sources)
        accepted_losses = {c["category"] for c in cps
                           if c["kind"] == "accepted" and c["category"] in LOSS_CATEGORIES}
        n = len(accepted_losses)
        severity = "low" if n == 0 else ("medium" if n == 1 else "high")
        result[num] = {"counterpoints": cps, "unknown_risks": unknowns,
                       "redteam_severity": severity, "accepted_loss_categories": sorted(accepted_losses)}

    # 能力首位（同点は馬番の小さい方）の暫定監査
    scored = [(horses[n]["step1"]["ability_score"], -n) for n in horses if horses[n]["step1"]["ability_score"] is not None]
    if scored:
        top = -max(scored)[1]
        cps = {c["category"]: c for c in result[top]["counterpoints"]}
        def state(cat):
            return cps[cat]["kind"] if cat in cps else "unknown"
        slots = {"展開": state("pace_failure"), "位置取り": state("position_failure"), "相手": state("opponent_risk")}
        result["top_ability_audit"] = {"horse": top, "slots": slots,
                                       "downgrade_eligible": all(v == "accepted" for v in slots.values()),
                                       "note": "暫定。確定は STEP7"}
    return {"status": "ok", "reason": None, "horses": result}
