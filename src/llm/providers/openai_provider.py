"""OpenAI APIプロバイダー"""

import logging
from typing import Dict, Any

from openai import OpenAI

from src.llm.providers.base_provider import LLMProvider
from src.data.weather_forecast import WeatherForecast
from src.data.comment_pair import CommentPair

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI APIを使用するプロバイダー"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        OpenAIプロバイダーの初期化。
        
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    def generate_comment(
        self,
        weather_data: WeatherForecast,
        past_comments: CommentPair,
        constraints: Dict[str, Any]
    ) -> str:
        """
        OpenAI APIを使用してコメントを生成。
        
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは天気予報のコメント作成の専門家です。短く、親しみやすいコメントを生成してください。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=50,
                n=1
            )
            
            # レスポンスからコメントを抽出
            generated_comment = response.choices[0].message.content.strip()
            
            # 改行や余分な記号を除去
            generated_comment = generated_comment.replace("\n", "").strip('"')
            
            logger.info(f"Generated comment: {generated_comment}")
            return generated_comment
            
        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise


# エクスポート
__all__ = ["OpenAIProvider"]
