"""
コメントペア選択ノード

過去コメントから適切なペアを選択するLangGraphノード
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, PastCommentCollection
from src.data.comment_pair import CommentPair, CommentPairCandidate
from src.data.weather_data import WeatherForecast
from src.algorithms.similarity_calculator import CommentSimilarityCalculator

logger = logging.getLogger(__name__)


def select_comment_pair_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    類似度計算により適切なコメントペアを選択
    
    Args:
        state: ワークフローの状態
        
    Returns:
        選択されたペアを含む更新された状態
    """
    logger.info("SelectCommentPairNode: コメントペア選択を開始")
    
    try:
        # 必要なデータの取得
        weather_data = state.get("weather_data")
        past_comments = state.get("past_comments", [])
        location_name = state.get("location_name", "")
        target_datetime = state.get("target_datetime", datetime.now())
        
        if not weather_data:
            raise ValueError("天気データが利用できません")
        
        if not past_comments:
            logger.warning("過去コメントが存在しません。デフォルトペアを使用します")
            state["selected_pair"] = _create_default_pair(weather_data)
            return state
        
        # コメントコレクションの作成
        collection = PastCommentCollection(past_comments)
        
        # 天気コメントとアドバイスを分離
        weather_comments = collection.filter_by_type("weather_comment").comments
        advice_comments = collection.filter_by_type("advice").comments
        
        if not weather_comments or not advice_comments:
            logger.warning("コメントタイプが不足しています。デフォルトペアを使用します")
            state["selected_pair"] = _create_default_pair(weather_data)
            return state
        
        # 類似度計算器の初期化
        calculator = CommentSimilarityCalculator()
        
        # ペア候補の生成と評価
        candidates = _generate_candidates(
            weather_comments,
            advice_comments,
            weather_data,
            location_name,
            target_datetime,
            calculator
        )
        
        # 最適なペアの選択
        best_pair = _select_best_pair(candidates)
        
        if not best_pair:
            logger.warning("適切なペアが見つかりません。デフォルトペアを使用します")
            state["selected_pair"] = _create_default_pair(weather_data)
            return state
        
        # 状態の更新
        state["selected_pair"] = best_pair.to_dict()
        logger.info(f"コメントペア選択完了: スコア={best_pair.similarity_score:.2f}")
        
        # デバッグ情報
        state["selection_metadata"] = {
            "total_candidates": len(candidates),
            "weather_comments_count": len(weather_comments),
            "advice_comments_count": len(advice_comments),
            "best_score": best_pair.similarity_score,
            "selection_reason": best_pair.selection_reason
        }
        
    except Exception as e:
        logger.error(f"コメントペア選択中にエラー: {str(e)}")
        state["errors"] = state.get("errors", []) + [f"SelectCommentPairNode: {str(e)}"]
        state["selected_pair"] = _create_default_pair(state.get("weather_data"))
    
    return state


def _generate_candidates(
    weather_comments: List[PastComment],
    advice_comments: List[PastComment],
    weather_data: WeatherForecast,
    location_name: str,
    target_datetime: datetime,
    calculator: CommentSimilarityCalculator
) -> List[CommentPairCandidate]:
    """
    コメントペア候補を生成
    """
    candidates = []
    
    # 効率化のため、上位N件のみを対象にする
    MAX_WEATHER_COMMENTS = 50
    MAX_ADVICE_COMMENTS = 50
    
    # 事前フィルタリング（天気条件で絞り込み）
    filtered_weather = _prefilter_comments(
        weather_comments, weather_data, location_name
    )[:MAX_WEATHER_COMMENTS]
    
    filtered_advice = _prefilter_comments(
        advice_comments, weather_data, location_name
    )[:MAX_ADVICE_COMMENTS]
    
    # ペア候補の生成
    for weather_comment in filtered_weather:
        for advice_comment in filtered_advice:
            # 同じ天気条件のペアを優先
            if _is_compatible_pair(weather_comment, advice_comment):
                # 各類似度を計算
                weather_sim = calculator.calculate_weather_similarity(
                    weather_data, weather_comment
                )
                temp_sim = calculator.calculate_temperature_similarity(
                    weather_data.temperature,
                    weather_comment.temperature
                )
                semantic_sim = calculator.calculate_semantic_similarity(
                    f"{weather_data.weather_description} {weather_data.temperature}度",
                    weather_comment.comment_text
                )
                temporal_sim = calculator.calculate_temporal_similarity(
                    target_datetime,
                    weather_comment.datetime
                )
                location_sim = calculator.calculate_location_similarity(
                    location_name,
                    weather_comment.location
                )
                
                candidate = CommentPairCandidate(
                    weather_comment=weather_comment,
                    advice_comment=advice_comment,
                    weather_similarity=weather_sim,
                    semantic_similarity=semantic_sim,
                    temporal_similarity=temporal_sim,
                    location_similarity=location_sim
                )
                
                # 閾値以上のスコアの候補のみ追加
                if candidate.total_score >= 0.3:
                    candidates.append(candidate)
    
    return candidates


def _prefilter_comments(
    comments: List[PastComment],
    weather_data: WeatherForecast,
    location_name: str
) -> List[PastComment]:
    """
    コメントを事前フィルタリング
    """
    filtered = []
    
    for comment in comments:
        # 基本的なフィルタリング条件
        if comment.is_valid():
            # 地点が一致または類似
            if _is_similar_location(comment.location, location_name):
                filtered.append(comment)
            # 天気条件が類似
            elif _is_similar_weather(comment.weather_condition, weather_data.weather_description):
                filtered.append(comment)
    
    return filtered


def _is_compatible_pair(
    weather_comment: PastComment,
    advice_comment: PastComment
) -> bool:
    """
    ペアとして適切かチェック
    """
    # 同じ天気条件
    if weather_comment.weather_condition == advice_comment.weather_condition:
        return True
    
    # 気温差が小さい
    if (weather_comment.temperature is not None and 
        advice_comment.temperature is not None):
        temp_diff = abs(weather_comment.temperature - advice_comment.temperature)
        if temp_diff <= 5.0:
            return True
    
    # 同じ地点
    if weather_comment.location == advice_comment.location:
        return True
    
    return False


def _select_best_pair(candidates: List[CommentPairCandidate]) -> Optional[CommentPair]:
    """
    最適なペアを選択
    """
    if not candidates:
        return None
    
    # スコアでソート
    sorted_candidates = sorted(
        candidates,
        key=lambda c: c.total_score,
        reverse=True
    )
    
    # 上位候補から選択
    best_candidate = sorted_candidates[0]
    
    # 選択理由の生成
    selection_reason = _generate_selection_reason(best_candidate)
    
    return best_candidate.to_comment_pair(selection_reason)


def _generate_selection_reason(candidate: CommentPairCandidate) -> str:
    """
    選択理由を生成
    """
    reasons = []
    
    if candidate.weather_similarity >= 0.8:
        reasons.append("天気条件が非常に類似")
    elif candidate.weather_similarity >= 0.5:
        reasons.append("天気条件が類似")
    
    if candidate.temporal_similarity >= 0.8:
        reasons.append("同じ時間帯")
    
    if candidate.location_similarity >= 0.8:
        reasons.append("同じ地点")
    
    if candidate.semantic_similarity >= 0.5:
        reasons.append("表現が類似")
    
    return "、".join(reasons) if reasons else "総合的に最適"


def _create_default_pair(weather_data: Optional[WeatherForecast]) -> Dict[str, Any]:
    """
    デフォルトのコメントペアを作成
    """
    weather_condition = "不明"
    if weather_data:
        weather_condition = weather_data.weather_description
    
    # デフォルトコメントマッピング
    default_comments = {
        "晴れ": {
            "weather": "いい天気ですね",
            "advice": "日差しにご注意を"
        },
        "曇り": {
            "weather": "曇り空ですね",
            "advice": "過ごしやすい一日を"
        },
        "雨": {
            "weather": "雨の一日です",
            "advice": "傘をお忘れなく"
        },
        "雪": {
            "weather": "雪が降っています",
            "advice": "暖かくしてお過ごしを"
        }
    }
    
    # 正規化
    normalized_condition = _normalize_weather_for_default(weather_condition)
    
    if normalized_condition in default_comments:
        comments = default_comments[normalized_condition]
    else:
        comments = default_comments["曇り"]  # デフォルト
    
    # ダミーのPastCommentオブジェクトを作成
    weather_comment = PastComment(
        comment_text=comments["weather"],
        comment_type="weather_comment",
        location="デフォルト",
        weather_condition=normalized_condition,
        temperature=20.0 if weather_data else None,
        datetime=datetime.now()
    )
    
    advice_comment = PastComment(
        comment_text=comments["advice"],
        comment_type="advice",
        location="デフォルト",
        weather_condition=normalized_condition,
        temperature=20.0 if weather_data else None,
        datetime=datetime.now()
    )
    
    pair = CommentPair(
        weather_comment=weather_comment,
        advice_comment=advice_comment,
        similarity_score=0.0,
        selection_reason="デフォルトペア（過去データなし）"
    )
    
    return pair.to_dict()


def _is_similar_location(loc1: str, loc2: str) -> bool:
    """地点が類似しているかチェック"""
    if not loc1 or not loc2:
        return False
    return loc1.strip() == loc2.strip() or loc1 in loc2 or loc2 in loc1


def _is_similar_weather(weather1: Optional[str], weather2: str) -> bool:
    """天気条件が類似しているかチェック"""
    if not weather1:
        return False
    
    # 簡易的な類似判定
    weather_groups = {
        "晴れ": ["晴", "快晴", "sunny", "clear"],
        "曇り": ["曇", "くもり", "cloudy"],
        "雨": ["雨", "降雨", "rain", "rainy"],
        "雪": ["雪", "降雪", "snow", "snowy"]
    }
    
    for group, keywords in weather_groups.items():
        if any(kw in weather1.lower() for kw in keywords) and \
           any(kw in weather2.lower() for kw in keywords):
            return True
    
    return False


def _normalize_weather_for_default(weather: str) -> str:
    """デフォルト用に天気を正規化"""
    weather_lower = weather.lower()
    
    if "晴" in weather or "sunny" in weather_lower or "clear" in weather_lower:
        return "晴れ"
    elif "雨" in weather or "rain" in weather_lower:
        return "雨"
    elif "雪" in weather or "snow" in weather_lower:
        return "雪"
    else:
        return "曇り"


# エクスポート
__all__ = ["select_comment_pair_node"]
