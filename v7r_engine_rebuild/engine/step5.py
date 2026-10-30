"""STEP5 勝利・敗北ルート（設計文書 0.1.0。閾値は docs/thresholds.md の確定値）。

- 各条件は text・sources・value を持つ。
- 閾値に達しない場合は「〜に達する根拠なし」と書く（空リストにしない）。
- 入力が無い場合は「入力不足のため判定不能」とし、status を incomplete にする。
- 1頭でも判定不能があれば incomplete。後続へ進ませない。
"""
from typing import Dict, List
from . import thresholds as T


def _cond(text, sources, value, ok):
    return {"text": text, "sources": sources, "value": value, "met": ok}


def _undetermined(what, sources):
    return {"text": f"入力不足のため{what}を判定不能", "sources": sources, "value": None, "met": None}


def ideal_pace(style_index):
    """通過位置指数から理想ペース（前寄り→スロー、後寄り→ハイ）。"""
    if style_index is None:
        return None
    if style_index < 0.35:
        return "スロー"
    if style_index > 0.65:
        return "ハイ"
    return "ミドル"


def step5_routes(horses: Dict[int, Dict]) -> Dict[int, Dict]:
    """horses: run_steps_0_to_4 の horses 部分（番号→結果）。"""
    out = {}
    for num, r in horses.items():
        ability = r["step1"]["ability_score"]
        wpr = r["step2"]["wpr_score"]
        svi = r["step3"]
        style = svi["style_index"]
        pace_dmg = svi["pace_damage"]
        fits = {"距離": svi["distance_fit"], "コース": svi["course_fit"], "馬場": svi["track_fit"]}
        wins, losses, incomplete = [], [], False

        # 勝利条件
        if ability is None:
            wins.append(_undetermined("能力による勝利条件", ["STEP1: 過去走の着順"])); incomplete = True
        elif ability >= T.WIN_ABILITY:
            wins.append(_cond(f"能力 {ability*10:.1f} 点（勝利条件 8.0 点以上を満たす）", ["STEP1"], ability, True))
        else:
            wins.append(_cond(f"能力 {ability*10:.1f} 点（勝利条件 8.0 点以上に達する根拠なし）", ["STEP1"], ability, False))

        known_fits = {k: v for k, v in fits.items() if v is not None}
        if not known_fits:
            wins.append(_undetermined("適性による勝利条件", ["STEP3: 距離・コース・馬場の適性"])); incomplete = True
        else:
            ok = [k for k, v in known_fits.items() if v >= T.FIT_MIN]
            if ok:
                wins.append(_cond(f"{'・'.join(ok)}適性が 5.0 点以上", ["STEP3"], known_fits, True))
            else:
                wins.append(_cond("適性が 5.0 点以上に達する根拠なし", ["STEP3"], known_fits, False))

        # 敗北条件
        if ability is None:
            losses.append(_undetermined("能力による敗北条件", ["STEP1"])); incomplete = True
        elif ability < T.LOSE_ABILITY:
            losses.append(_cond(f"能力 {ability*10:.1f} 点（敗北条件 5.0 点未満を満たす）", ["STEP1"], ability, True))
        else:
            losses.append(_cond(f"能力 {ability*10:.1f} 点（敗北条件 5.0 点未満に達する根拠なし）", ["STEP1"], ability, False))

        if pace_dmg is None:
            losses.append(_undetermined("展開被害による敗北条件", ["STEP3: 想定ペース・通過位置"])); incomplete = True
        elif pace_dmg >= T.PACE_DAMAGE_COLLAPSE:
            losses.append(_cond(f"展開被害 {pace_dmg*10:.1f} 点（6.0 点以上で崩れる）", ["STEP3"], pace_dmg, True))
        else:
            losses.append(_cond(f"展開被害 {pace_dmg*10:.1f} 点（6.0 点以上に達する根拠なし）", ["STEP3"], pace_dmg, False))

        if wpr is None:
            losses.append(_undetermined("位置取りによる敗北条件", ["STEP2: 通過順位"])); incomplete = True
        elif wpr < T.FIT_MIN:
            losses.append(_cond(f"WPR {wpr*10:.1f} 点（5.0 点未満。位置を取れない）", ["STEP2"], wpr, True))
        else:
            losses.append(_cond(f"WPR {wpr*10:.1f} 点（5.0 点未満に達する根拠なし）", ["STEP2"], wpr, False))

        if not known_fits:
            losses.append(_undetermined("適性不足による敗北条件", ["STEP3"])); incomplete = True
        else:
            bad = [k for k, v in known_fits.items() if v < T.FIT_MIN]
            if bad:
                losses.append(_cond(f"{'・'.join(bad)}適性が 5.0 点未満", ["STEP3"], known_fits, True))
            else:
                losses.append(_cond("適性が 5.0 点未満に達する根拠なし", ["STEP3"], known_fits, False))

        # 理想ペース・相手
        ip = ideal_pace(style)
        if ip is None:
            incomplete = True
        out[num] = {"ideal_pace": ip, "wins": wins, "losses": losses,
                    "key_opponents": [], "status": None}

    # 相手（能力差 1.0 以内・理想位置が重なる）
    for num, r in horses.items():
        a = r["step1"]["ability_score"]
        al = r["step2"]["allowed_range"]
        for other, ro in horses.items():
            if other == num or a is None:
                continue
            b = ro["step1"]["ability_score"]
            bl = ro["step2"]["allowed_range"]
            if b is None or al is None or bl is None:
                continue
            overlap = not (al[1] < bl[0] or bl[1] < al[0])
            if abs(a - b) <= T.OPPONENT_GAP and overlap:
                out[num]["key_opponents"].append(other)

    # 入力の利用率（7入力）と status
    for num, r in horses.items():
        svi = r["step3"]
        inputs = [r["step1"]["ability_score"], r["step2"]["wpr_score"], svi["style_index"],
                  svi["pace_benefit"], svi["distance_fit"], svi["course_fit"], svi["track_fit"]]
        out[num]["route_confidence"] = round(sum(v is not None for v in inputs) / 7, 4)
        out[num]["status"] = "incomplete" if incomplete_for(out[num]) else "complete"
    return out


def incomplete_for(route):
    return any(c["met"] is None for c in route["wins"] + route["losses"]) or route["ideal_pace"] is None
