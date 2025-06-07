"""
コメントペアデータクラス

天気コメントとアドバイスのペアを管理するデータクラス
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

from src.data.past_comment import PastComment


@dataclass
class CommentPair:
    """
    天気コメントとアドバイスのペア
    
    Attributes:
        weather_comment: 天気に関するコメント
        advice_comment: アドバイスコメント
        similarity_score: 類似度スコア (0.0-1.0)
        selection_reason: 選択理由の説明
        metadata: その他のメタデータ
    """
    weather_comment: PastComment
    advice_comment: PastComment
    similarity_score: float
    selection_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後の検証"""
        # スコアの範囲チェック
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError(f"類似度スコアは0.0-1.0の範囲である必要があります: {self.similarity_score}")
        
        # コメントタイプの検証
        if self.weather_comment.comment_type != "weather_comment":
            raise ValueError("weather_commentのタイプが不正です")
        if self.advice_comment.comment_type != "advice":
            raise ValueError("advice_commentのタイプが不正です")
    
    @property
    def average_temperature(self) -> Optional[float]:
        """ペアの平均気温を取得"""
        temps = []
        if self.weather_comment.temperature is not None:
            temps.append(self.weather_comment.temperature)
        if self.advice_comment.temperature is not None:
            temps.append(self.advice_comment.temperature)
        
        return sum(temps) / len(temps) if temps else None
    
    @property
    def common_weather_condition(self) -> Optional[str]:
        """共通の天気条件を取得"""
        if self.weather_comment.weather_condition == self.advice_comment.weather_condition:
            return self.weather_comment.weather_condition
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "weather_comment": self.weather_comment.to_dict(),
            "advice_comment": self.advice_comment.to_dict(),
            "similarity_score": self.similarity_score,
            "selection_reason": self.selection_reason,
            "average_temperature": self.average_temperature,
            "common_weather_condition": self.common_weather_condition,
            "metadata": self.metadata
        }


@dataclass
class CommentPairCandidate:
    """
    コメントペア候補（評価前）
    
    Attributes:
        weather_comment: 天気コメント候補
        advice_comment: アドバイスコメント候補
        weather_similarity: 天気条件の類似度
        semantic_similarity: 意味的類似度
        temporal_similarity: 時間的類似度
        location_similarity: 地点の類似度
    """
    weather_comment: PastComment
    advice_comment: PastComment
    weather_similarity: float = 0.0
    semantic_similarity: float = 0.0
    temporal_similarity: float = 0.0
    location_similarity: float = 0.0
    
    @property
    def total_score(self) -> float:
        """総合スコアを計算"""
        # 重み付けは設定可能にする
        weights = {
            "weather": 0.4,
            "semantic": 0.3,
            "temporal": 0.2,
            "location": 0.1
        }
        
        return (
            self.weather_similarity * weights["weather"] +
            self.semantic_similarity * weights["semantic"] +
            self.temporal_similarity * weights["temporal"] +
            self.location_similarity * weights["location"]
        )
    
    def to_comment_pair(self, selection_reason: str) -> CommentPair:
        """CommentPairに変換"""
        return CommentPair(
            weather_comment=self.weather_comment,
            advice_comment=self.advice_comment,
            similarity_score=self.total_score,
            selection_reason=selection_reason,
            metadata={
                "weather_similarity": self.weather_similarity,
                "semantic_similarity": self.semantic_similarity,
                "temporal_similarity": self.temporal_similarity,
                "location_similarity": self.location_similarity
            }
        )
