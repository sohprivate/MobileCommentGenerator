"""
出力ノード

最終結果を整形してJSON形式で出力するLangGraphノード
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


def output_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    最終結果をJSON形式で出力
    
    Args:
        state: ワークフローの状態
        
    Returns:
        出力形式に整形された状態
    """
    logger.info("OutputNode: 出力処理を開始")
    
    try:
        # 実行時間の計算
        execution_start = state.get("execution_start_time")
        execution_end = datetime.now()
        execution_time_ms = 0
        
        if execution_start:
            execution_time_delta = execution_end - execution_start
            execution_time_ms = int(execution_time_delta.total_seconds() * 1000)
        
        # 最終コメントの確定
        final_comment = _determine_final_comment(state)
        state["final_comment"] = final_comment
        
        # メタデータの生成
        generation_metadata = _create_generation_metadata(state, execution_time_ms)
        state["generation_metadata"] = generation_metadata
        
        # 出力データの構築
        output_data = {
            "final_comment": final_comment,
            "generation_metadata": generation_metadata
        }
        
        # オプション情報の追加
        if state.get("include_debug_info", False):
            output_data["debug_info"] = _create_debug_info(state)
        
        # JSON形式への変換
        state["output_json"] = json.dumps(output_data, ensure_ascii=False, indent=2)
        
        # 成功ログ
        logger.info(
            f"出力処理完了: comment_length={len(final_comment)}, "
            f"execution_time={execution_time_ms}ms, "
            f"retry_count={state.get('retry_count', 0)}"
        )
        
        # クリーンアップ
        _cleanup_state(state)
        
        state["output_processed"] = True
        
    except Exception as e:
        logger.error(f"出力処理中にエラー: {str(e)}")
        state["errors"] = state.get("errors", []) + [f"OutputNode: {str(e)}"]
        state["output_processed"] = False
        
        # エラー時のフォールバック出力
        state["output_json"] = json.dumps({
            "error": "出力処理中にエラーが発生しました",
            "final_comment": state.get("final_comment", "素敵な一日をお過ごしください"),
            "generation_metadata": {
                "error": str(e),
                "execution_time_ms": 0
            }
        }, ensure_ascii=False)
    
    return state


def _determine_final_comment(state: CommentGenerationState) -> str:
    """
    最終コメントを確定
    
    優先順位:
    1. generated_comment（LLM生成）
    2. selected_pair の weather_comment
    3. デフォルトコメント
    """
    # LLM生成コメントがある場合
    if state.get("generated_comment"):
        return state["generated_comment"]
    
    # 選択されたペアがある場合
    selected_pair = state.get("selected_pair")
    if selected_pair and isinstance(selected_pair, dict):
        weather_comment = selected_pair.get("weather_comment", {})
        if isinstance(weather_comment, dict) and weather_comment.get("comment_text"):
            return weather_comment["comment_text"]
    
    # 天気データに基づくデフォルト
    weather_data = state.get("weather_data", {})
    if weather_data:
        return _create_default_comment(weather_data)
    
    # 最終フォールバック
    return "今日も素敵な一日をお過ごしください"


def _create_generation_metadata(state: CommentGenerationState, execution_time_ms: int) -> Dict[str, Any]:
    """
    生成メタデータを作成
    """
    metadata = {
        "execution_time_ms": execution_time_ms,
        "retry_count": state.get("retry_count", 0),
        "request_id": state.get("execution_context", {}).get("request_id", "unknown"),
        "generation_timestamp": datetime.now().isoformat(),
        "location_name": state.get("location_name", "不明"),
        "target_datetime": state.get("target_datetime", datetime.now()).isoformat()
            if state.get("target_datetime") else None,
        "llm_provider": state.get("llm_provider", "none")
    }
    
    # 天気情報の追加
    weather_data = state.get("weather_data", {})
    if weather_data:
        metadata.update({
            "weather_condition": weather_data.get("weather_description", "不明"),
            "temperature": weather_data.get("temperature"),
            "humidity": weather_data.get("humidity"),
            "wind_speed": weather_data.get("wind_speed")
        })
    
    # 選択されたコメント情報
    selected_pair = state.get("selected_pair", {})
    if selected_pair:
        metadata["selected_past_comments"] = _extract_selected_comments(selected_pair)
        metadata["similarity_score"] = selected_pair.get("similarity_score", 0.0)
        metadata["selection_reason"] = selected_pair.get("selection_reason", "")
    
    # 検証結果
    validation_result = state.get("validation_result", {})
    if validation_result:
        metadata["validation_passed"] = validation_result.get("is_valid", False)
        metadata["validation_score"] = validation_result.get("total_score", 0.0)
    
    # エラーと警告
    if state.get("errors"):
        metadata["errors"] = state["errors"]
    if state.get("warnings"):
        metadata["warnings"] = state["warnings"]
    
    # ユーザー設定
    user_preferences = state.get("user_preferences", {})
    if user_preferences:
        metadata["style"] = user_preferences.get("style", "casual")
        metadata["length"] = user_preferences.get("length", "medium")
    
    return metadata


def _extract_selected_comments(selected_pair: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    選択されたコメント情報を抽出
    """
    comments = []
    
    # 天気コメント
    weather_comment = selected_pair.get("weather_comment", {})
    if isinstance(weather_comment, dict) and weather_comment.get("comment_text"):
        comments.append({
            "text": weather_comment["comment_text"],
            "type": "weather_comment",
            "temperature": weather_comment.get("temperature"),
            "weather_condition": weather_comment.get("weather_condition")
        })
    
    # アドバイスコメント
    advice_comment = selected_pair.get("advice_comment", {})
    if isinstance(advice_comment, dict) and advice_comment.get("comment_text"):
        comments.append({
            "text": advice_comment["comment_text"],
            "type": "advice",
            "temperature": advice_comment.get("temperature"),
            "weather_condition": advice_comment.get("weather_condition")
        })
    
    return comments


def _create_default_comment(weather_data: Dict[str, Any]) -> str:
    """
    天気データに基づくデフォルトコメントを生成
    """
    weather_desc = weather_data.get("weather_description", "").lower()
    temp = weather_data.get("temperature", 20)
    
    # 天気条件別デフォルト
    if "晴" in weather_desc or "clear" in weather_desc or "sunny" in weather_desc:
        if temp > 25:
            return "暑い一日になりそうです。水分補給を忘れずに！"
        elif temp < 10:
            return "晴れていますが寒いです。暖かくしてお出かけください"
        else:
            return "気持ちの良い晴れの日です"
    elif "雨" in weather_desc or "rain" in weather_desc:
        return "雨の一日です。傘をお忘れなく"
    elif "雪" in weather_desc or "snow" in weather_desc:
        return "雪が降っています。足元にお気をつけください"
    elif "曇" in weather_desc or "cloud" in weather_desc:
        return "曇り空の一日です"
    else:
        return "今日も一日がんばりましょう"


def _create_debug_info(state: CommentGenerationState) -> Dict[str, Any]:
    """
    デバッグ情報を作成
    """
    return {
        "state_keys": list(state.keys()),
        "retry_history": state.get("evaluation_history", []),
        "node_execution_times": state.get("node_execution_times", {}),
        "api_call_count": state.get("api_call_count", 0),
        "cache_hits": state.get("cache_hits", 0),
        "total_past_comments": len(state.get("past_comments", [])),
        "workflow_version": state.get("execution_context", {}).get("api_version", "unknown")
    }


def _cleanup_state(state: CommentGenerationState):
    """
    不要な中間データをクリーンアップ
    
    メモリ使用量を削減するため、大きな中間データを削除
    """
    # 大きなデータの削除候補
    cleanup_keys = [
        "past_comments",  # 過去コメントの大量データ
        "all_weather_data",  # 詳細な天気データ
        "candidate_pairs",  # 評価前の候補ペア
        "evaluation_details",  # 詳細な評価情報
    ]
    
    for key in cleanup_keys:
        if key in state and isinstance(state.get(key), (list, dict)):
            # サイズが大きい場合のみ削除
            if len(str(state[key])) > 10000:  # 10KB以上
                logger.debug(f"クリーンアップ: {key} を削除")
                del state[key]


# エクスポート
__all__ = ["output_node"]
