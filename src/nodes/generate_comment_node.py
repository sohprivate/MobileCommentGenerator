"""天気コメント生成ノード

LLMを使用して天気情報と過去コメントを基にコメントを生成する。
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from langgraph.graph import node

from src.data.comment_generation_state import CommentGenerationState
from src.llm.llm_manager import LLMManager
from src.data.weather_forecast import WeatherForecast
from src.data.comment_pair import CommentPair

logger = logging.getLogger(__name__)


@node
def generate_comment_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    LLMを使用してコメントを生成するノード。
    
    Args:
        state: 現在のワークフロー状態
        
    Returns:
        更新された状態（generated_comment追加）
    """
    try:
        logger.info("Starting comment generation")
        
        # 必要なデータの確認
        weather_data = state.get("weather_data")
        selected_pair = state.get("selected_pair")
        llm_provider = state.get("llm_provider", "openai")
        
        if not weather_data:
            raise ValueError("Weather data is required for comment generation")
        
        if not selected_pair:
            raise ValueError("Selected comment pair is required for generation")
        
        # LLMマネージャーの初期化
        llm_manager = LLMManager(provider=llm_provider)
        
        # 制約条件の設定
        constraints = {
            "max_length": 15,
            "ng_words": _get_ng_words(),
            "time_period": _get_time_period(state.get("target_datetime")),
            "season": _get_season(state.get("target_datetime"))
        }
        
        # コメント生成
        generated_comment = llm_manager.generate_comment(
            weather_data=weather_data,
            past_comments=selected_pair,
            constraints=constraints
        )
        
        logger.info(f"Generated comment: {generated_comment}")
        
        # 状態の更新
        state["generated_comment"] = generated_comment
        state["generation_metadata"] = state.get("generation_metadata", {})
        state["generation_metadata"].update({
            "llm_provider": llm_provider,
            "generation_timestamp": datetime.now().isoformat(),
            "constraints_applied": constraints
        })
        
        return state
        
    except Exception as e:
        logger.error(f"Error in generate_comment_node: {str(e)}")
        state["errors"] = state.get("errors", [])
        state["errors"].append({
            "node": "generate_comment",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        
        # フォールバックコメント
        state["generated_comment"] = _get_fallback_comment(weather_data)
        
        return state


def _get_ng_words() -> list:
    """NGワードリストを取得"""
    # TODO: 設定ファイルから読み込み
    return [
        "災害", "危険", "注意", "警告",
        "絶対", "必ず", "間違いない",
        "くそ", "やばい", "最悪"
    ]


def _get_time_period(target_datetime: Optional[datetime]) -> str:
    """時間帯を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    
    hour = target_datetime.hour
    if 5 <= hour < 10:
        return "朝"
    elif 10 <= hour < 17:
        return "昼"
    elif 17 <= hour < 21:
        return "夕方"
    else:
        return "夜"


def _get_season(target_datetime: Optional[datetime]) -> str:
    """季節を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    
    month = target_datetime.month
    if month in [3, 4, 5]:
        return "春"
    elif month in [6, 7, 8]:
        return "夏"
    elif month in [9, 10, 11]:
        return "秋"
    else:
        return "冬"


def _get_fallback_comment(weather_data: Optional[WeatherForecast]) -> str:
    """フォールバックコメントを生成"""
    if not weather_data:
        return "今日も一日頑張ろう"
    
    # シンプルな天気ベースのコメント
    weather_comments = {
        "晴れ": "晴れて気持ちいい",
        "曇り": "曇り空ですね",
        "雨": "傘をお忘れなく",
        "雪": "雪に注意です"
    }
    
    weather_condition = weather_data.weather_description
    for key, comment in weather_comments.items():
        if key in weather_condition:
            return comment
    
    return "今日も良い一日を"


# エクスポート
__all__ = ["generate_comment_node"]
