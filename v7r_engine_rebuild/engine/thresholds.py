"""閾値の集約（すべて仮。設計文書 0.1.0 の値を移したもの）。"""

FINISH_SCORE_MAX_RANK = 18          # 着順スコア = (18 - 着順) / 17
FINISH_SCORE_DENOM = 17
RECENT_WEIGHTS = (0.5, 0.3, 0.2)    # 直近最大3走の重み（新しい順を仮定）
IDEAL_TOP_RANK = 3                  # 理想位置の算出に使う着順（3着内）
IDEAL_FALLBACK_RANK = 5             # 3着内の走が無い場合は5着内で代用
POOR_RANK = 8                       # 苦戦位置の算出に使う着順（8着以下）
WPR_TOLERANCE = 2                   # 許容位置 = 理想位置 ± 2
DISTANCE_WINDOW_M = 200             # 距離適性の範囲（±200m）
PACE_MIDDLE_VALUE = 0.5             # ミドルペースの恩恵・被害（ルール値）
MAX_FIELD_SIZE = 18                # JRA の出走頭数の上限（実際に走った頭数。取消・除外は除く）

# ---- 10 点表示の基準（内部は 0〜1。値は 10 で割って持つ） ----
def to_internal(points10):
    return points10 / 10.0

WIN_ABILITY = to_internal(8.0)        # 勝利条件（能力）  仮
LOSE_ABILITY = to_internal(5.0)       # 敗北条件（能力）  仮
OPPONENT_GAP = to_internal(1.0)       # 能力差 1.0 以内    設計文書（0.10）
PACE_DAMAGE_COLLAPSE = to_internal(6.0)  # 展開被害 6.0 以上 設計文書（0.60）
FIT_MIN = to_internal(5.0)            # 適性・WPR・騎手の下限 設計文書（0.50）
CONTRADICTION_ABILITY = to_internal(8.0)  # 設計文書（0.80）
# 通過位置（番手・18頭換算）
FRONT_MAX_BAN = 5                     # 前寄り: 5番手以内
BACK_MIN_BAN = 12                     # 後寄り: 12番手以降
