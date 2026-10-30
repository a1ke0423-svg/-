"""入力データの型。欠損は補完せず None のまま保持する。"""
from dataclasses import dataclass, field
from typing import List, Optional

VALID_SURFACES = {"芝", "ダ"}
VALID_PACE = {"ハイ", "ミドル", "スロー", None}


@dataclass(frozen=True)
class PastResult:
    date: str                       # 例: "2026-10-25"（新しい順で並べる前提）
    venue: str
    surface: str                    # "芝" or "ダ"
    distance: int                   # メートル
    finish: Optional[int]           # 着順（取消・除外は None）
    corner_path: List[int] = field(default_factory=list)  # 道中の通過順位列（判明分のみ）
    field_size: Optional[int] = None  # 頭数（無ければ None。H-4 の未解消項目）


@dataclass(frozen=True)
class Horse:
    number: int
    name: str
    weight: Optional[float] = None
    past: List[PastResult] = field(default_factory=list)
    jockey: Optional[str] = None
    jockey_metrics: Optional[dict] = None  # 指標5種。無ければ None（補完しない）


@dataclass(frozen=True)
class RaceCard:
    race_id: str
    date: str
    venue: str
    surface: str
    distance: int
    track_condition: Optional[str]   # 不明なら None
    pace_label: Optional[str]        # "ハイ"/"ミドル"/"スロー"/None（未入力）
    horses: List[Horse]
