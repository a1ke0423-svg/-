"""STEP0〜4 の再構築（設計文書 0.1.0 の式に従う）。

- 欠損は補完しない。None と警告で後続へ渡す。
- 能力と SVI は別項目として保持する（上書きしない）。
- STEP1〜4 は experimental。
"""
from typing import Dict, List, Optional
from . import thresholds as T
from .models import RaceCard, Horse, PastResult, VALID_SURFACES, VALID_PACE


def finish_score(finish: Optional[int]) -> Optional[float]:
    if finish is None:
        return None
    return max(0.0, min(1.0, (T.FINISH_SCORE_MAX_RANK - finish) / T.FINISH_SCORE_DENOM))


# ---------- STEP0 ----------
def step0_quality(card: RaceCard) -> List[str]:
    """欠損と矛盾の一覧を返す。補完はしない。"""
    w = []
    if card.surface not in VALID_SURFACES:
        w.append(f"芝ダ区分が不正または不明: {card.surface}")
    if card.track_condition is None:
        w.append("馬場: 不明（推測で補わない）")
    if card.pace_label not in VALID_PACE:
        w.append(f"想定ペースの値が不正: {card.pace_label}")
    if card.pace_label is None:
        w.append("想定ペース: 未入力")
    if not card.horses:
        w.append("出走馬がいない")
    nums = [h.number for h in card.horses]
    if len(set(nums)) != len(nums):
        w.append("馬番が重複")
    for h in card.horses:
        if h.weight is None:
            w.append(f"馬{h.number}: 馬体重 不明")
        if h.jockey is None:
            w.append(f"馬{h.number}: 騎手 不明")
        if not h.past:
            w.append(f"馬{h.number}: 過去走 なし")
        for p in h.past:
            if p.finish is None:
                w.append(f"馬{h.number}: 過去走 {p.date} の着順 不明")
            if p.field_size is None:
                w.append(f"馬{h.number}: 過去走 {p.date} の頭数 不明（H-4）")
            else:
                if not (1 <= p.field_size <= T.MAX_FIELD_SIZE):
                    w.append(f"矛盾: 馬{h.number} 過去走 {p.date} の頭数 {p.field_size} は範囲外（1〜{T.MAX_FIELD_SIZE}）")
                if p.finish is not None and p.finish > p.field_size:
                    w.append(f"矛盾: 馬{h.number} 過去走 {p.date} の着順 {p.finish} が頭数 {p.field_size} を超えている")
            if not p.corner_path:
                w.append(f"馬{h.number}: 過去走 {p.date} の通過順位 不明")
            if p.track_condition is None:
                w.append(f"馬{h.number}: 過去走 {p.date} の馬場状態 不明")
    return w


# ---------- STEP1 ----------
def step1_ability(horse: Horse) -> Dict:
    """能力スコア（直近最大3走の加重平均。欠けた走は重みを正規化）。順位は付けない。"""
    runs = horse.past[:3]
    scores = [finish_score(p.finish) for p in runs]
    usable = [(s, w) for s, w in zip(scores, T.RECENT_WEIGHTS) if s is not None]
    if not usable:
        return {"ability_score": None, "recent_level": None, "growth": None}
    total_w = sum(w for _, w in usable)
    ability = sum(s * w for s, w in usable) / total_w
    recent = scores[0]
    rest = [s for s in scores[1:] if s is not None]
    growth = (recent - sum(rest) / len(rest)) if (recent is not None and rest) else None
    return {"ability_score": round(ability, 4), "recent_level": recent,
            "growth": None if growth is None else round(growth, 4)}


# ---------- STEP2 ----------
def _first_corner(p: PastResult) -> Optional[int]:
    return p.corner_path[0] if p.corner_path else None


def step2_wpr(horse: Horse) -> Dict:
    """WPR: 理想位置・許容位置・苦戦位置と、許容位置に入った走の割合。
    仮定: 1走の通過位置は corner_path の先頭（最初に判明した通過順位）で代表する。"""
    top = [_first_corner(p) for p in horse.past
           if p.finish is not None and p.finish <= T.IDEAL_TOP_RANK and _first_corner(p)]
    if not top:
        top = [_first_corner(p) for p in horse.past
               if p.finish is not None and p.finish <= T.IDEAL_FALLBACK_RANK and _first_corner(p)]
    if not top:
        return {"ideal_range": None, "allowed_range": None, "poor_range": None, "wpr_score": None}
    lo, hi = min(top), max(top)
    allowed = (max(1, lo - T.WPR_TOLERANCE), hi + T.WPR_TOLERANCE)
    poor_pos = [_first_corner(p) for p in horse.past
                if p.finish is not None and p.finish >= T.POOR_RANK and _first_corner(p)]
    poor = (min(poor_pos), max(poor_pos)) if poor_pos else None
    measurable = [_first_corner(p) for p in horse.past if _first_corner(p)]
    if not measurable:
        wpr = None
    else:
        inside = sum(1 for c in measurable if allowed[0] <= c <= allowed[1])
        wpr = round(inside / len(measurable), 4)
    return {"ideal_range": (lo, hi), "allowed_range": allowed,
            "poor_range": poor, "wpr_score": wpr}


# ---------- STEP3 ----------
def _style_index(p: PastResult) -> Optional[float]:
    """0（先頭）〜1（後方）。頭数が無いと換算できないので None（H-4）。"""
    if not p.corner_path or p.field_size is None or p.field_size < 2:
        return None
    mean_pos = sum(p.corner_path) / len(p.corner_path)
    return max(0.0, min(1.0, (mean_pos - 1) / (p.field_size - 1)))


def step3_svi(horse: Horse, card: RaceCard) -> Dict:
    idx = [s for s in (_style_index(p) for p in horse.past) if s is not None]
    style = sum(idx) / len(idx) if idx else None
    warnings = []
    pace_benefit = pace_damage = None
    if style is None:
        warnings.append("通過位置指数: 算出不能（通過順位または頭数が不足）")
    if card.pace_label == "ハイ" and style is not None:
        pace_benefit, pace_damage = style, 1 - style
    elif card.pace_label == "スロー" and style is not None:
        pace_benefit, pace_damage = 1 - style, style
    elif card.pace_label == "ミドル" and style is not None:
        pace_benefit, pace_damage = T.PACE_MIDDLE_VALUE, T.PACE_MIDDLE_VALUE
    else:
        warnings.append("展開恩恵・被害: 想定ペース未入力または算出不能のため None")

    def fit(filter_fn):
        vals = [finish_score(p.finish) for p in horse.past if filter_fn(p) and p.finish is not None]
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    track_fit = None
    if card.track_condition is not None:
        track_fit = fit(lambda p: p.track_condition == card.track_condition)
    else:
        warnings.append("馬場適正: 当日の馬場が不明のため None")
    course_fit = fit(lambda p: p.venue == card.venue and p.surface == card.surface)
    surface_fit = fit(lambda p: p.surface == card.surface)
    distance_fit = fit(lambda p: abs(p.distance - card.distance) <= T.DISTANCE_WINDOW_M)

    comps = [c for c in (pace_benefit,
                         None if pace_damage is None else 1 - pace_damage,
                         course_fit, surface_fit, distance_fit) if c is not None]
    overall = round(sum(comps) / len(comps), 4) if comps else None
    return {"style_index": None if style is None else round(style, 4),
            "pace_benefit": pace_benefit, "pace_damage": pace_damage,
            "course_fit": course_fit, "surface_fit": surface_fit,
            "distance_fit": distance_fit, "track_fit": track_fit,
            "overall_svi": overall, "warnings": warnings}


# ---------- STEP4 ----------
JOCKEY_KEYS = ["positioning_reproducibility", "timing_reproducibility", "course_fit",
               "horse_fit", "tactical_flexibility"]


def step4_jockey(horse: Horse) -> Dict:
    """入力値をそのまま採用する。計算はしない。無い指標は None。"""
    m = horse.jockey_metrics or {}
    out = {k: m.get(k) for k in JOCKEY_KEYS}
    out["warnings"] = [f"騎手指標 {k} 未入力" for k in JOCKEY_KEYS if m.get(k) is None]
    return out


def run_steps_0_to_4(card: RaceCard) -> Dict:
    result = {"step0_warnings": step0_quality(card), "horses": {}}
    for h in card.horses:
        result["horses"][h.number] = {
            "name": h.name,
            "step1": step1_ability(h),
            "step2": step2_wpr(h),
            "step3": step3_svi(h, card),
            "step4": step4_jockey(h),
        }
    return result
