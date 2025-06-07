"""Anthropic Claude APIプロバイダー"""

import logging
from typing import Dict, Any

from anthropic import Anthropic

from src.llm.providers.base_provider import LLMProvider
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude APIを使用するプロバイダー"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Anthropicプロバイダーの初期化。
        
        Args:
            api_key: Anthropic APIキー
            model: 使用するモデル名
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Anthropic provider with model: {model}")
    
    def generate_comment(
        self,
        weather_data: WeatherForecast,
        past_comments: CommentPair,
        constraints: Dict[str, Any]
    ) -> str:
        """
        Claude APIを使用してコメントを生成。
        
        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件
            
        Returns:
            生成されたコメント
        """
        try:
            # プロンプトの構築
            prompt = self._build_prompt(weather_data, past_comments, constraints)
            
            # APIリクエスト
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                temperature=0.7,
                system="あなたは天気予報のコメント作成の専門家です。短く、親しみやすいコメントを生成してください。",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # レスポンスからコメントを抽出
            generated_comment = response.content[0].text.strip()
            
            # 改行や余分な記号を除去
            generated_comment = generated_comment.replace("\n", "").strip('"')
            
            logger.info(f"Generated comment: {generated_comment}")
            return generated_comment
            
        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            raise


# エクスポート
__all__ = ["AnthropicProvider"]
