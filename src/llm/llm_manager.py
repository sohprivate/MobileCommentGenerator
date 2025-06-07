"""LLMマネージャー

複数のLLMプロバイダーを統一的に管理するマネージャークラス。
"""

import os
from typing import Dict, Any, Optional
import logging

from src.data.weather_forecast import WeatherForecast
from src.data.comment_pair import CommentPair
from src.llm.providers.base_provider import LLMProvider
from src.llm.providers.openai_provider import OpenAIProvider
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)


class LLMManager:
    """LLMプロバイダーを管理するマネージャークラス"""
    
    def __init__(self, provider: str = "openai"):
        """
        LLMマネージャーの初期化。
        
        Args:
            provider: 使用するプロバイダー名 ("openai", "gemini", "anthropic")
        """
        self.provider_name = provider
        self.provider = self._initialize_provider(provider)
    
    def _initialize_provider(self, provider_name: str) -> LLMProvider:
        """プロバイダーを初期化"""
        providers = {
            "openai": self._init_openai,
            "gemini": self._init_gemini,
            "anthropic": self._init_anthropic
        }
        
        if provider_name not in providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return providers[provider_name]()
    
    def _init_openai(self) -> OpenAIProvider:
        """OpenAIプロバイダーを初期化"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        return OpenAIProvider(api_key=api_key, model=model)
    
    def _init_gemini(self) -> GeminiProvider:
        """Geminiプロバイダーを初期化"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        model = os.getenv("GEMINI_MODEL", "gemini-pro")
        return GeminiProvider(api_key=api_key, model=model)
    
    def _init_anthropic(self) -> AnthropicProvider:
        """Anthropicプロバイダーを初期化"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        return AnthropicProvider(api_key=api_key, model=model)
    
    def generate_comment(
        self,
        weather_data: WeatherForecast,
        past_comments: CommentPair,
        constraints: Dict[str, Any]
    ) -> str:
        """
        天気コメントを生成する。
        
        Args:
            weather_data: 天気予報データ
            past_comments: 過去のコメントペア
            constraints: 制約条件
            
        Returns:
            生成されたコメント
        """
        try:
            logger.info(f"Generating comment using {self.provider_name}")
            
            # プロバイダーを使用してコメント生成
            comment = self.provider.generate_comment(
                weather_data=weather_data,
                past_comments=past_comments,
                constraints=constraints
            )
            
            # 基本的な検証
            if len(comment) > constraints.get("max_length", 15):
                logger.warning(f"Generated comment exceeds max length: {comment}")
                # 切り詰め
                comment = comment[:constraints.get("max_length", 15)]
            
            return comment
            
        except Exception as e:
            logger.error(f"Error generating comment: {str(e)}")
            raise
    
    def switch_provider(self, provider_name: str):
        """プロバイダーを切り替える"""
        logger.info(f"Switching provider from {self.provider_name} to {provider_name}")
        self.provider_name = provider_name
        self.provider = self._initialize_provider(provider_name)


# エクスポート
__all__ = ["LLMManager"]
