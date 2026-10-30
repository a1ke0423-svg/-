"""STEP11 Blue Team（工程の監査。分析内容は評価しない）。

確認項目（設計文書 0.1.0 の STEP11）:
 1. 全頭評価したか
 2. STEP を飛ばしていないか
 3. 人気・オッズ情報が混入していないか
 4. 未知と不適性を混同していないか
 5. 能力評価と再現性評価を混同していないか
 6. 能力首位馬を理由なく降格していないか
 7. 9 シナリオ結果と最終順位が矛盾していないか

結果は pass / review（人の確認が必要）/ fail。fail があれば後続へ進めない。
"""
from typing import Dict, List

MARKET_KEYS = {"odds", "オッズ", "popularity", "人気", "人気順", "予想印", "印"}
REQUIRED_STEPS = ["step1", "step2", "step3", "step4"]


def audit_inputs(raw: Dict) -> List[Dict]:
    """入力（生データ）に市場情報が混ざっていないか。"""
    found = []
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if str(k).lower() in {m.lower() for m in MARKET_KEYS} or k in MARKET_KEYS:
                    found.append(f"{path}{k}")
                walk(v, f"{path}{k}.")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}].")
    walk(raw)
    return [{"item": "3. 市場情報の混入", "status": "fail" if found else "pass",
             "detail": ("混入: " + ", ".join(found)) if found else "なし"}]


def audit(horses: Dict[int, Dict], step5: Dict, redteam: Dict, step7: Dict,
          step9: Dict, step10: Dict, overview_missing: Dict[int, List[str]]) -> List[Dict]:
    items = []

    # 1. 全頭評価
    missing = [n for n in horses if any(s not in horses[n] for s in REQUIRED_STEPS)]
    no_prob = [n for n in horses if n not in step10["horses"]]
    ok = not missing and not no_prob
    items.append({"item": "1. 全頭評価", "status": "pass" if ok else "fail",
                  "detail": "全馬の STEP1〜4・STEP10 あり" if ok else f"欠落: {missing + no_prob}"})

    # 2. STEP を飛ばしていないか
    skipped = []
    if redteam.get("status") == "blocked":
        skipped.append(f"STEP6 が blocked（{redteam.get('reason')}）")
    if not step5 or any(r.get("status") is None for r in step5.values()):
        skipped.append("STEP5 の結果が不完全")
    items.append({"item": "2. STEP の飛ばし", "status": "fail" if skipped else "pass",
                  "detail": "; ".join(skipped) if skipped else "STEP0〜10 の順に実施"})

    # 4. 未知と不適性の混同（None の項目は、必ず「不明」として残っているか）
    confused = []
    for n, r in horses.items():
        for key, label in [("distance_fit", "距離適性"), ("course_fit", "コース適性"), ("track_fit", "馬場適正")]:
            if r["step3"].get(key) is None and label not in overview_missing.get(n, []):
                confused.append(f"馬{n} {label}")
    items.append({"item": "4. 未知と不適性の混同", "status": "fail" if confused else "pass",
                  "detail": "未知は不明として残っている" if not confused else f"未知が不明扱いされていない: {confused}"})

    # 5. 能力評価と再現性評価の混同（STEP10 で再現性が別項目か）
    mixed = [n for n in horses if "reproducibility_wpr" not in step10["horses"].get(n, {})
             or "win_prob" not in step10["horses"].get(n, {})]
    items.append({"item": "5. 能力と再現性の混同", "status": "fail" if mixed else "pass",
                  "detail": "能力と再現性は別項目" if not mixed else f"混在の疑い: {mixed}"})

    # 6. 能力首位の理由なし降格（STEP7 の首位が能力の最大と一致するか）
    ability_top = None
    scored = [(horses[n]["step1"]["ability_score"], -n) for n in horses if horses[n]["step1"]["ability_score"] is not None]
    if scored:
        ability_top = -max(scored)[1]
    step7_top = step7["order"][0] if step7.get("order") else None
    status6 = "pass" if (ability_top is None or step7_top == ability_top) else "fail"
    items.append({"item": "6. 能力首位の理由なし降格", "status": status6,
                  "detail": "能力首位と STEP7 の首位が一致" if status6 == "pass" else f"不一致: 能力首位 {ability_top}, STEP7 {step7_top}"})

    # 7. 9 シナリオ結果と最終順位の矛盾（人の確認が必要な場合は review）
    most = step9.get("most_wins")
    if most is None:
        items.append({"item": "7. 9シナリオと順位の矛盾", "status": "review",
                      "detail": "最多勝馬が決まらない（1着が無い）。確認が必要"})
    elif most != step7_top:
        items.append({"item": "7. 9シナリオと順位の矛盾", "status": "review",
                      "detail": f"最多勝馬 {most} と能力首位 {step7_top} が異なる。説明が必要"})
    else:
        items.append({"item": "7. 9シナリオと順位の矛盾", "status": "pass",
                      "detail": "最多勝馬と能力首位が一致"})
    return items


def summary(items: List[Dict]) -> str:
    if any(i["status"] == "fail" for i in items):
        return "fail（後続へ進めない）"
    if any(i["status"] == "review" for i in items):
        return "review（人の確認が必要）"
    return "pass"
