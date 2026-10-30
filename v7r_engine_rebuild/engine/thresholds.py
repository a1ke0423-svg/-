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
