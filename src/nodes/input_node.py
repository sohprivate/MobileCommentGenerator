"""
入力ノード

ユーザー入力を受け取り、初期状態を設定するLangGraphノード
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import pytz

from src.data.comment_generation_state import CommentGenerationState
from src.data.location import Location

logger = logging.getLogger(__name__)


def input_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    ユーザー入力を受け取り、初期stateを設定
    
    Args:
        state: ワークフローの状態
        
    Returns:
        初期化された状態
    """
    logger.info("InputNode: 入力処理を開始")
    
    try:
        # 必須パラメータの検証
        location_name = state.get("location_name")
        if not location_name:
            raise ValueError("location_name（地点名）は必須パラメータです")
        
        # デフォルト値の設定
        target_datetime = state.get("target_datetime")
        if not target_datetime:
            # 日本時間で現在時刻を設定
            jst = pytz.timezone('Asia/Tokyo')
            target_datetime = datetime.now(jst)
            state["target_datetime"] = target_datetime
            logger.info(f"target_datetimeが未指定のため、現在時刻を使用: {target_datetime}")
        
        # Location オブジェクトの作成
        location = _create_location(location_name)
        state["location"] = location.to_dict()
        
        # LLMプロバイダーのデフォルト設定
        if not state.get("llm_provider"):
            state["llm_provider"] = "openai"
            logger.info("llm_providerが未指定のため、デフォルト'openai'を使用")
        
        # 初期化
        state["retry_count"] = 0
        state["errors"] = []
        state["warnings"] = []
        state["execution_start_time"] = datetime.now()
        
        # ユーザー設定の初期化
        if not state.get("user_preferences"):
            state["user_preferences"] = _get_default_preferences()
        
        # 実行コンテキストの設定
        state["execution_context"] = {
            "request_id": _generate_request_id(),
            "api_version": "1.0.0",
            "environment": state.get("environment", "production")
        }
        
        # 入力パラメータのログ
        logger.info(
            f"入力パラメータ: location={location_name}, "
            f"datetime={target_datetime}, "
            f"llm_provider={state['llm_provider']}"
        )
        
        # バリデーション
        _validate_input_parameters(state)
        
        state["input_processed"] = True
        
    except Exception as e:
        logger.error(f"入力処理中にエラー: {str(e)}")
        state["errors"] = state.get("errors", []) + [f"InputNode: {str(e)}"]
        state["input_processed"] = False
        # エラーでも続行できるように最低限の初期化
        _initialize_minimal_state(state)
    
    return state


def _create_location(location_name: str) -> Location:
    """
    地点名からLocationオブジェクトを作成
    
    実際の実装では地点マスタやジオコーディングAPIを使用
    """
    # 地点マスタ（簡易版）
    location_master = {
        "稚内": {
            "latitude": 45.4158,
            "longitude": 141.6733,
            "region": "北海道",
            "prefecture": "北海道"
        },
        "東京": {
            "latitude": 35.6762,
            "longitude": 139.6503,
            "region": "関東",
            "prefecture": "東京都"
        },
        "大阪": {
            "latitude": 34.6937,
            "longitude": 135.5023,
            "region": "関西",
            "prefecture": "大阪府"
        },
        "那覇": {
            "latitude": 26.2124,
            "longitude": 127.6792,
            "region": "沖縄",
            "prefecture": "沖縄県"
        }
    }
    
    # 地点情報の取得
    if location_name in location_master:
        info = location_master[location_name]
        return Location(
            name=location_name,
            latitude=info["latitude"],
            longitude=info["longitude"],
            region=info["region"],
            prefecture=info["prefecture"]
        )
    else:
        # 登録されていない地点の場合はデフォルト（東京）を使用
        logger.warning(f"未登録の地点名: {location_name}。東京の座標を使用します")
        return Location(
            name=location_name,
            latitude=35.6762,
            longitude=139.6503,
            region="不明",
            prefecture="不明"
        )


def _get_default_preferences() -> Dict[str, Any]:
    """
    デフォルトのユーザー設定を取得
    """
    return {
        "style": "casual",  # casual/formal/friendly
        "length": "medium",  # short/medium/long
        "emoji_usage": True,
        "weather_focus": "balanced",  # weather/advice/balanced
        "positivity": "positive",  # positive/neutral/realistic
        "personalization": True,
        "seasonal_awareness": True,
        "time_awareness": True,
        "evaluation_weights": None  # Use default weights
    }


def _generate_request_id() -> str:
    """
    ユニークなリクエストIDを生成
    """
    import uuid
    return str(uuid.uuid4())


def _validate_input_parameters(state: CommentGenerationState):
    """
    入力パラメータの詳細検証
    """
    # 地点名の検証
    location_name = state.get("location_name", "")
    if len(location_name) > 50:
        raise ValueError("地点名は50文字以内で指定してください")
    
    if not location_name.replace(" ", "").replace("　", ""):
        raise ValueError("地点名が空白のみです")
    
    # 日時の検証
    target_datetime = state.get("target_datetime")
    if target_datetime:
        # 未来すぎる日時のチェック（7日後まで）
        max_future = datetime.now() + timedelta(days=7)
        if target_datetime > max_future:
            state["warnings"].append("7日以上先の日時が指定されています")
        
        # 過去すぎる日時のチェック（1年前まで）
        min_past = datetime.now() - timedelta(days=365)
        if target_datetime < min_past:
            state["warnings"].append("1年以上前の日時が指定されています")
    
    # LLMプロバイダーの検証
    valid_providers = ["openai", "gemini", "anthropic"]
    llm_provider = state.get("llm_provider", "").lower()
    if llm_provider not in valid_providers:
        raise ValueError(
            f"無効なLLMプロバイダー: {llm_provider}。"
            f"有効な値: {', '.join(valid_providers)}"
        )
    
    # ユーザー設定の検証
    preferences = state.get("user_preferences", {})
    if preferences:
        _validate_user_preferences(preferences)


def _validate_user_preferences(preferences: Dict[str, Any]):
    """
    ユーザー設定の検証
    """
    # スタイルの検証
    valid_styles = ["casual", "formal", "friendly"]
    style = preferences.get("style", "casual")
    if style not in valid_styles:
        preferences["style"] = "casual"
        logger.warning(f"無効なstyle '{style}' が指定されました。デフォルト 'casual' を使用")
    
    # 長さの検証
    valid_lengths = ["short", "medium", "long"]
    length = preferences.get("length", "medium")
    if length not in valid_lengths:
        preferences["length"] = "medium"
        logger.warning(f"無効なlength '{length}' が指定されました。デフォルト 'medium' を使用")
    
    # ブール値の検証
    bool_keys = ["emoji_usage", "personalization", "seasonal_awareness", "time_awareness"]
    for key in bool_keys:
        if key in preferences and not isinstance(preferences[key], bool):
            preferences[key] = True
            logger.warning(f"{key} はブール値である必要があります。デフォルト True を使用")


def _initialize_minimal_state(state: CommentGenerationState):
    """
    エラー時の最小限の状態初期化
    """
    if not state.get("location_name"):
        state["location_name"] = "東京"
    
    if not state.get("target_datetime"):
        state["target_datetime"] = datetime.now()
    
    if not state.get("llm_provider"):
        state["llm_provider"] = "openai"
    
    state["retry_count"] = 0
    state["input_processed"] = False


# エクスポート
__all__ = ["input_node"]
