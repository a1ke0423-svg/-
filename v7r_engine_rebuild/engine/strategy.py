"""STEP12 Strategy Team（俯瞰の要約。新しい評価は入れない）。

設計文書の項目: 現在地・最重要論点・最大リスク・最も信頼できる評価・推奨判断・非推奨判断。
- 推奨判断は「STEP13（予測固定）へ進むか」の判断だけ。買い目ではない。
- 最終順位を動かす場合は、具体的な説明を要求する（設計文書 STEP12）。
"""
from typing import Dict, List


def strategy_summary(horses: Dict[int, Dict], step7: Dict, step9: Dict, step10: Dict,
                     redteam: Dict, blue_status: str) -> Dict:
    # 現在地
    done = ["STEP0〜4（情報・能力・WPR・SVI・騎手）", "STEP5（勝利・敗北ルート）"]
    done.append("STEP6（Red Team）: " + ("blocked" if redteam.get("status") == "blocked" else "実施"))
    done += ["STEP7（能力順位）", "STEP8（WPR順位）", "STEP9（9シナリオ）", "STEP10（着順確率）",
             f"STEP11（Blue Team）: {blue_status}"]
    now = {"完了": done, "未実施": ["STEP13（最終固定）"]}

    # 最重要論点（能力首位と最多勝馬）
    top = step7["order"][0] if step7.get("order") else None
    most = step9.get("most_wins")
    points = [f"能力首位: 馬{top}" if top is not None else "能力首位: 不明"]
    points.append(f"9シナリオ最多勝: 馬{most}" if most is not None else "9シナリオ最多勝: 不明（1着なし）")
    if top is not None and most is not None and top != most:
        points.append("能力首位と最多勝が異なる。説明が必要（STEP12・STEP13 で確認）")

    # 最大リスク（敗北カテゴリが成立した数が多い馬。高の馬）
    risks = []
    for n in sorted(k for k in redteam.get("horses", {}) if isinstance(k, int)):
        h = redteam["horses"][n]
        if h["redteam_severity"] in ("中", "高"):
            risks.append(f"馬{n}: 危険度 {h['redteam_severity']}（{', '.join(h['accepted_loss_categories'])}）")
    unknown_total = sum(len(redteam["horses"][n]["unknown_risks"]) for n in redteam.get("horses", {})
                        if isinstance(n, int))
    risks.append(f"未知リスクの件数: {unknown_total}")

    # 最も信頼できる評価（入力が最もそろっている指標）
    def coverage(key_fn):
        vals = [key_fn(horses[n]) for n in horses]
        return sum(v is not None for v in vals) / len(vals) if vals else 0
    cov = {
        "能力順位（STEP1）": coverage(lambda h: h["step1"]["ability_score"]),
        "WPR（STEP2）": coverage(lambda h: h["step2"]["wpr_score"]),
        "SVI（STEP3）": coverage(lambda h: h["step3"]["overall_svi"]),
    }
    best = max(cov, key=lambda k: cov[k])
    trust = {"最も信頼できる評価": best, "入力の充足率": {k: round(v, 2) for k, v in cov.items()}}

    # 推奨判断・非推奨判断
    if blue_status.startswith("pass"):
        rec = "STEP13（予測固定）へ進む"
    elif blue_status.startswith("review"):
        rec = "人の確認を経てから STEP13 へ進む"
    else:
        rec = "STEP13 へ進まない（工程の修正が必要）"
    not_rec = [
        "予測固定の前に、オッズ・人気を見て順位を変えること",
        "最終順位を動かす場合に、具体的な説明を省くこと（能力首位の降格には、負ける展開・位置取り・相手が必要）",
        "買い目を先に決めて、予測を後から合わせること",
    ]
    return {"現在地": now, "最重要論点": points, "最大リスク": risks, "最も信頼できる評価": trust,
            "推奨判断": rec, "非推奨判断": not_rec, "note": "俯瞰の要約。買い目ではない"}
