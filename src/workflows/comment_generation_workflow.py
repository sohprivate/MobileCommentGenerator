"""
天気コメント生成ワークフロー

LangGraphを使用した天気コメント生成のメインワークフロー実装
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langgraph import StateGraph
from langgraph.graph import END

from src.data.comment_generation_state import CommentGenerationState
from src.nodes.weather_forecast_node import fetch_weather_forecast_node
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node
from src.nodes.generate_comment_node import generate_comment_node

# 一時的なモックノード（実装待ち）
from src.nodes.mock_nodes import (
    mock_input_node,
    mock_select_comment_pair_node,
    mock_evaluate_candidate_node,
    mock_output_node
)


# 定数
MAX_RETRY_COUNT = 5


def should_retry(state: CommentGenerationState) -> str:
    """
    リトライが必要かどうかを判定
    
    Args:
        state: 現在のワークフロー状態
        
    Returns:
        "retry" または "continue" の文字列
    """
    # リトライ上限チェック
    if state.get("retry_count", 0) >= MAX_RETRY_COUNT:
        return "continue"
    
    # バリデーション結果をチェック
    validation_result = state.get("validation_result", {})
    if validation_result and not validation_result.get("is_valid", True):
        return "retry"
    
    return "continue"


def create_comment_generation_workflow() -> StateGraph:
    """
    天気コメント生成ワークフローを構築
    
    Returns:
        構築されたLangGraphワークフロー
    """
    # ワークフローの初期化
    workflow = StateGraph(CommentGenerationState)
    
    # ノードの追加
    workflow.add_node("input", mock_input_node)
    workflow.add_node("fetch_forecast", fetch_weather_forecast_node)
    workflow.add_node("retrieve_comments", retrieve_past_comments_node)
    workflow.add_node("select_pair", mock_select_comment_pair_node)
    workflow.add_node("evaluate", mock_evaluate_candidate_node)
    workflow.add_node("generate", generate_comment_node)
    workflow.add_node("output", mock_output_node)
    
    # エッジの追加（通常フロー）
    workflow.add_edge("input", "fetch_forecast")
    workflow.add_edge("fetch_forecast", "retrieve_comments")
    workflow.add_edge("retrieve_comments", "select_pair")
    workflow.add_edge("select_pair", "evaluate")
    
    # 条件付きエッジ（リトライループ）
    workflow.add_conditional_edges(
        "evaluate",
        should_retry,
        {
            "retry": "select_pair",
            "continue": "generate"
        }
    )
    
    workflow.add_edge("generate", "output")
    workflow.add_edge("output", END)
    
    # エントリーポイントの設定
    workflow.set_entry_point("input")
    
    return workflow.compile()


def run_comment_generation(
    location_name: str,
    target_datetime: Optional[datetime] = None,
    llm_provider: str = "openai",
    **kwargs
) -> Dict[str, Any]:
    """
    コメント生成ワークフローを実行
    
    Args:
        location_name: 地点名
        target_datetime: 対象日時（デフォルト: 現在時刻）
        llm_provider: LLMプロバイダー（openai/gemini/anthropic）
        **kwargs: その他のオプション
        
    Returns:
        生成結果を含む辞書
    """
    # ワークフローの構築
    workflow = create_comment_generation_workflow()
    
    # 初期状態の準備
    initial_state = {
        "location_name": location_name,
        "target_datetime": target_datetime or datetime.now(),
        "llm_provider": llm_provider,
        "retry_count": 0,
        "errors": [],
        "warnings": [],
        **kwargs
    }
    
    # ワークフローの実行
    try:
        result = workflow.invoke(initial_state)
        return {
            "success": True,
            "final_comment": result.get("final_comment"),
            "generation_metadata": result.get("generation_metadata", {}),
            "execution_time_ms": result.get("execution_time_ms"),
            "retry_count": result.get("retry_count", 0)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "final_comment": None,
            "generation_metadata": {}
        }


# エクスポート
__all__ = [
    "create_comment_generation_workflow",
    "run_comment_generation"
]
