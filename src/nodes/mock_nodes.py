"""
モックノード実装

実装待ちのノードのモック版
"""

from typing import Dict, Any
import logging
from datetime import datetime

from src.data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


def mock_input_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    入力ノードのモック実装

    ユーザー入力を受け取り、初期状態を設定
    """
    logger.info(
        f"InputNode: 地点={state.get('location_name')}, 時刻={state.get('target_datetime')}"
    )

    # 入力検証（簡易版）
    if not state.get("location_name"):
        state["errors"] = state.get("errors", []) + ["地点名が指定されていません"]
        raise ValueError("地点名が必須です")

    # 実行開始時刻を記録
    state["start_time"] = datetime.now()

    return state


def mock_select_comment_pair_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    コメントペア選択ノードのモック実装

    過去コメントから適切なペアを選択（モック）
    """
    logger.info("SelectCommentPairNode: モック実装でダミーデータを返します")

    # モックデータ
    state["selected_pair"] = {
        "weather_comment": {
            "text": "爽やかな朝ですね",
            "type": "weather_comment",
            "weather_condition": "晴れ",
            "temperature": 20.0,
        },
        "advice": {
            "text": "日焼け対策を忘れずに",
            "type": "advice",
            "weather_condition": "晴れ",
            "temperature": 20.0,
        },
        "similarity_score": 0.85,
        "selection_reason": "天気条件が類似",
    }

    return state


def mock_evaluate_candidate_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    候補評価ノードのモック実装

    生成されたコメントを評価（モック）
    """
    logger.info("EvaluateCandidateNode: モック実装で常に成功を返します")

    # リトライカウントをインクリメント（テスト用）
    retry_count = state.get("retry_count", 0)

    # 最初の2回は失敗させる（リトライループのテスト）
    if retry_count < 2:
        state["validation_result"] = {
            "is_valid": False,
            "error_type": "length_error",
            "error_message": "文字数が15文字を超えています（モックエラー）",
            "retry_count": retry_count + 1,
        }
        state["retry_count"] = retry_count + 1
        logger.warning(f"評価失敗（モック）: リトライ {retry_count + 1}/{5}")
    else:
        # 3回目以降は成功
        state["validation_result"] = {"is_valid": True, "error_type": None, "error_message": None}
        logger.info("評価成功（モック）")

    return state


def mock_output_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    出力ノードのモック実装

    最終結果を整形して出力
    """
    logger.info("OutputNode: 結果を整形します")

    # 実行時間の計算
    if state.get("start_time"):
        execution_time = (datetime.now() - state["start_time"]).total_seconds() * 1000
        state["execution_time_ms"] = int(execution_time)

    # 最終的な出力データの整形
    state["generation_metadata"] = {
        "execution_time_ms": state.get("execution_time_ms", 0),
        "retry_count": state.get("retry_count", 0),
        "weather_condition": state.get("weather_data", {}).get("weather_condition", "不明"),
        "temperature": state.get("weather_data", {}).get("temperature", 0),
        "selected_past_comments": [
            state.get("selected_pair", {}).get("weather_comment", {}),
            state.get("selected_pair", {}).get("advice", {}),
        ],
        "validation_passed": state.get("validation_result", {}).get("is_valid", False),
        "llm_provider": state.get("llm_provider", "openai"),
        "location": state.get("location_name"),
        "timestamp": datetime.now().isoformat(),
    }

    logger.info(
        f"生成完了: {state.get('final_comment')} (実行時間: {state.get('execution_time_ms')}ms)"
    )

    return state


# エクスポート
__all__ = [
    "mock_input_node",
    "mock_select_comment_pair_node",
    "mock_evaluate_candidate_node",
    "mock_output_node",
]
