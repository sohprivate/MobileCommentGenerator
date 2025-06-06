"""
GenerateCommentNode - LLMを使用してコメントを生成するLangGraphノード

このモジュールは、過去コメントと現在の天気情報を基に、
適切な天気コメントをLLMで生成するLangGraphノードを提供します。
"""

from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

from ..llm.llm_client import LLMClientFactory
from ..llm.prompt_builder import CommentPromptBuilder
from ..data.comment_generation_state import CommentGenerationState

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """コメント生成結果"""
    generated_comment: str
    provider_used: str
    generation_time_ms: int
    is_fallback: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def generate_comment_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    LLMを使用してコメントを生成するLangGraphノード
    
    Args:
        state: コメント生成の状態データ
        
    Returns:
        CommentGenerationState: 生成されたコメントが追加された状態
    """
    logger.info(f"コメント生成開始 - 地点: {state.location_name}")
    
    try:
        # LLMクライアント作成
        llm_provider = getattr(state, 'llm_provider', 'openai')
        client_factory = LLMClientFactory()
        client = client_factory.create_client(llm_provider)
        
        # プロンプト構築
        prompt_builder = CommentPromptBuilder()
        prompt = prompt_builder.build_prompt(
            weather_data=state.weather_data,
            past_comments=state.past_comments,
            location=state.location_name,
            selected_pair=getattr(state, 'selected_pair', None)
        )
        
        logger.debug(f"プロンプト構築完了 - 長さ: {len(prompt)} 文字")
        
        # コメント生成
        start_time = datetime.now()
        generated_comment = client.generate_comment(prompt)
        end_time = datetime.now()
        generation_time = int((end_time - start_time).total_seconds() * 1000)
        
        # 結果作成
        result = GenerationResult(
            generated_comment=generated_comment,
            provider_used=llm_provider,
            generation_time_ms=generation_time,
            metadata={
                'prompt_length': len(prompt),
                'generated_at': datetime.now().isoformat(),
                'weather_condition': state.weather_data.weather_description if state.weather_data else None,
                'temperature': state.weather_data.temperature if state.weather_data else None
            }
        )
        
        # stateに結果を格納
        state.generated_comment = generated_comment
        state.generation_metadata.update({
            'llm_provider': llm_provider,
            'generation_time_ms': generation_time,
            'generated_at': result.metadata['generated_at']
        })
        
        logger.info(f"コメント生成成功 - {generation_time}ms")
        logger.debug(f"生成コメント: {generated_comment}")
        
    except Exception as e:
        logger.error(f"コメント生成エラー: {str(e)}")
        
        # フォールバック処理
        fallback_comment = _get_fallback_comment(state)
        
        state.generated_comment = fallback_comment
        state.generation_metadata.update({
            'llm_provider': 'fallback',
            'generation_error': str(e),
            'is_fallback': True,
            'generated_at': datetime.now().isoformat()
        })
        
        logger.info(f"フォールバックコメント使用: {fallback_comment}")
    
    return state


def _get_fallback_comment(state: CommentGenerationState) -> str:
    """
    エラー時のフォールバックコメントを取得
    
    Args:
        state: コメント生成の状態データ
        
    Returns:
        str: フォールバックコメント
    """
    # 天気情報があれば天気に応じたデフォルトコメント
    if state.weather_data:
        weather_condition = state.weather_data.weather_description
        
        fallback_comments = {
            '晴れ': '爽やかな一日ですね',
            '曇り': '過ごしやすい天気です',
            '雨': '雨の日も素敵です',
            '雪': '雪景色が美しいです'
        }
        
        for condition, comment in fallback_comments.items():
            if condition in weather_condition:
                return comment
    
    # 過去コメントがあれば最初のコメントを使用
    if state.past_comments:
        return state.past_comments[0].comment_text
    
    # デフォルトコメント
    return '今日も良い一日を'


def generate_comment_with_fallback(state: CommentGenerationState) -> CommentGenerationState:
    """
    フォールバック機能付きコメント生成
    
    複数のLLMプロバイダーでリトライしてコメント生成を試行します。
    
    Args:
        state: コメント生成の状態データ
        
    Returns:
        CommentGenerationState: 生成されたコメントが追加された状態
    """
    providers = ['openai', 'anthropic', 'gemini']
    original_provider = getattr(state, 'llm_provider', 'openai')
    
    # オリジナルプロバイダーを最初に試行
    if original_provider in providers:
        providers.remove(original_provider)
        providers.insert(0, original_provider)
    
    for provider in providers:
        try:
            state.llm_provider = provider
            return generate_comment_node(state)
        except Exception as e:
            logger.warning(f"プロバイダー {provider} での生成失敗: {str(e)}")
            continue
    
    # 全てのプロバイダーで失敗した場合のフォールバック
    logger.error("全LLMプロバイダーでの生成に失敗")
    state.generated_comment = _get_fallback_comment(state)
    state.generation_metadata.update({
        'llm_provider': 'fallback_all_failed',
        'generation_error': 'All LLM providers failed',
        'is_fallback': True,
        'generated_at': datetime.now().isoformat()
    })
    
    return state
