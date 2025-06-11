"""
LLMプロバイダーのテスト
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

from src.llm.providers.openai_provider import OpenAIProvider
from src.llm.providers.gemini_provider import GeminiProvider
from src.llm.providers.anthropic_provider import AnthropicProvider
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment


class TestOpenAIProvider:
    """OpenAIプロバイダーのテストクラス"""

    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ"""
        weather_data = WeatherForecast(
            location="東京", weather_description="晴れ", temperature=25.0
        )

        weather_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="爽やかな朝です",
            comment_type="weather_comment",
        )

        advice_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="日焼け対策を",
            comment_type="advice",
        )

        comment_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.95,
            selection_reason="高い類似度",
        )

        constraints = {"max_length": 15, "ng_words": ["災害", "危険"], "time_period": "朝"}

        return weather_data, comment_pair, constraints

    @patch("src.llm.providers.openai_provider.OpenAI")
    def test_openai_provider_init(self, mock_openai_class):
        """OpenAIプロバイダー初期化のテスト"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")

        mock_openai_class.assert_called_once_with(api_key="test-key")
        assert provider.model == "gpt-4"

    @patch("src.llm.providers.openai_provider.OpenAI")
    def test_openai_generate_comment(self, mock_openai_class, sample_data):
        """OpenAIでのコメント生成テスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "今日は爽やかですね"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key")
        weather_data, comment_pair, constraints = sample_data

        result = provider.generate_comment(
            weather_data=weather_data, past_comments=comment_pair, constraints=constraints
        )

        assert result == "今日は爽やかですね"
        mock_client.chat.completions.create.assert_called_once()

        # API呼び出しパラメータの検証
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 50


class TestGeminiProvider:
    """Geminiプロバイダーのテストクラス"""

    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ（OpenAIと同じ）"""
        weather_data = WeatherForecast(
            location="東京", weather_description="晴れ", temperature=25.0
        )

        weather_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="爽やかな朝です",
            comment_type="weather_comment",
        )

        advice_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="日焼け対策を",
            comment_type="advice",
        )

        comment_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.95,
            selection_reason="高い類似度",
        )

        constraints = {"max_length": 15, "ng_words": ["災害", "危険"], "time_period": "朝"}

        return weather_data, comment_pair, constraints

    @patch("src.llm.providers.gemini_provider.genai")
    def test_gemini_provider_init(self, mock_genai):
        """Geminiプロバイダー初期化のテスト"""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key", model="gemini-pro")

        mock_genai.configure.assert_called_once_with(api_key="test-key")
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        assert provider.model_name == "gemini-pro"

    @patch("src.llm.providers.gemini_provider.genai")
    def test_gemini_generate_comment(self, mock_genai, sample_data):
        """Geminiでのコメント生成テスト"""
        # モックの設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "今日は爽やかですね"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        provider = GeminiProvider(api_key="test-key")
        weather_data, comment_pair, constraints = sample_data

        result = provider.generate_comment(
            weather_data=weather_data, past_comments=comment_pair, constraints=constraints
        )

        assert result == "今日は爽やかですね"
        mock_model.generate_content.assert_called_once()


class TestAnthropicProvider:
    """Anthropicプロバイダーのテストクラス"""

    @pytest.fixture
    def sample_data(self):
        """テスト用サンプルデータ（OpenAIと同じ）"""
        weather_data = WeatherForecast(
            location="東京", weather_description="晴れ", temperature=25.0
        )

        weather_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="爽やかな朝です",
            comment_type="weather_comment",
        )

        advice_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="日焼け対策を",
            comment_type="advice",
        )

        comment_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.95,
            selection_reason="高い類似度",
        )

        constraints = {"max_length": 15, "ng_words": ["災害", "危険"], "time_period": "朝"}

        return weather_data, comment_pair, constraints

    @patch("src.llm.providers.anthropic_provider.Anthropic")
    def test_anthropic_provider_init(self, mock_anthropic_class):
        """Anthropicプロバイダー初期化のテスト"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-opus-20240229")

        mock_anthropic_class.assert_called_once_with(api_key="test-key")
        assert provider.model == "claude-3-opus-20240229"

    @patch("src.llm.providers.anthropic_provider.Anthropic")
    def test_anthropic_generate_comment(self, mock_anthropic_class, sample_data):
        """Anthropicでのコメント生成テスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "今日は爽やかですね"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(api_key="test-key")
        weather_data, comment_pair, constraints = sample_data

        result = provider.generate_comment(
            weather_data=weather_data, past_comments=comment_pair, constraints=constraints
        )

        assert result == "今日は爽やかですね"
        mock_client.messages.create.assert_called_once()

        # API呼び出しパラメータの検証
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-opus-20240229"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 50


class TestPromptBuilding:
    """プロンプト構築のテスト"""

    def test_build_prompt(self):
        """プロンプト構築メソッドのテスト"""
        from src.llm.providers.base_provider import LLMProvider

        # テスト用の具象クラス
        class TestProvider(LLMProvider):
            def generate_comment(self, weather_data, past_comments, constraints):
                return ""

        provider = TestProvider()

        weather_data = WeatherForecast(
            location="東京", weather_description="晴れ", temperature=25.0
        )

        weather_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="爽やかな朝です",
            comment_type="weather_comment",
        )

        advice_comment = PastComment(
            location="東京",
            weather_condition="晴れ",
            temperature=24.0,
            comment_text="日焼け対策を",
            comment_type="advice",
        )

        comment_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=0.95,
            selection_reason="高い類似度",
        )

        constraints = {"max_length": 15, "ng_words": ["災害", "危険"], "time_period": "朝"}

        prompt = provider._build_prompt(weather_data, comment_pair, constraints)

        # プロンプトに必要な要素が含まれているか確認
        assert "東京" in prompt
        assert "晴れ" in prompt
        assert "25.0" in prompt
        assert "爽やかな朝です" in prompt
        assert "日焼け対策を" in prompt
        assert "15文字以内" in prompt
        assert "災害、危険" in prompt
