"""
GenerateCommentNodeのテスト

このモジュールは、GenerateCommentNodeの機能をテストします。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# テスト対象モジュールのインポート用にパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.nodes.generate_comment_node import (
    generate_comment_node,
    generate_comment_with_fallback,
    GenerationResult,
    _get_fallback_comment
)
from src.data.comment_generation_state import CommentGenerationState, create_test_state


@pytest.fixture
def mock_weather_data():
    """モック天気データ"""
    weather_data = Mock()
    weather_data.weather_description = "晴れ"
    weather_data.temperature = 20.5
    weather_data.humidity = 60
    weather_data.wind_speed = 2.5
    return weather_data


@pytest.fixture
def mock_past_comments():
    """モック過去コメント"""
    comment1 = Mock()
    comment1.comment_text = "爽やかな朝です"
    comment1.comment_type = "weather_comment"
    
    comment2 = Mock()
    comment2.comment_text = "日焼け対策を"
    comment2.comment_type = "advice"
    
    return [comment1, comment2]


@pytest.fixture
def test_state(mock_weather_data, mock_past_comments):
    """テスト用状態"""
    state = create_test_state()
    state.weather_data = mock_weather_data
    state.past_comments = mock_past_comments
    return state


class TestGenerateCommentNode:
    """GenerateCommentNodeのテスト"""
    
    @patch('src.nodes.generate_comment_node.LLMClientFactory')
    @patch('src.nodes.generate_comment_node.CommentPromptBuilder')
    def test_generate_comment_node_success(self, mock_prompt_builder, mock_client_factory, test_state):
        """正常なコメント生成のテスト"""
        # モック設定
        mock_client = Mock()
        mock_client.generate_comment.return_value = "爽やかな朝ですね"
        mock_client_factory.return_value.create_client.return_value = mock_client
        
        mock_builder = Mock()
        mock_builder.build_prompt.return_value = "test prompt"
        mock_prompt_builder.return_value = mock_builder
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 検証
        assert result_state.generated_comment == "爽やかな朝ですね"
        assert 'llm_provider' in result_state.generation_metadata
        assert 'generation_time_ms' in result_state.generation_metadata
        assert result_state.generation_metadata['llm_provider'] == 'openai'
        
        # モック呼び出し確認
        mock_client_factory.return_value.create_client.assert_called_once_with('openai')
        mock_client.generate_comment.assert_called_once_with("test prompt")
    
    @patch('src.nodes.generate_comment_node.LLMClientFactory')
    def test_generate_comment_node_failure_fallback(self, mock_client_factory, test_state):
        """LLM生成失敗時のフォールバック処理テスト"""
        # モック設定（例外発生）
        mock_client = Mock()
        mock_client.generate_comment.side_effect = Exception("API Error")
        mock_client_factory.return_value.create_client.return_value = mock_client
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 検証
        assert result_state.generated_comment is not None  # フォールバックコメントが設定される
        assert result_state.generation_metadata['llm_provider'] == 'fallback'
        assert result_state.generation_metadata['is_fallback'] is True
        assert 'generation_error' in result_state.generation_metadata
    
    def test_get_fallback_comment_with_weather(self, test_state):
        """天気データありでのフォールバックコメントテスト"""
        fallback_comment = _get_fallback_comment(test_state)
        
        # 晴れの天気データがあるので、対応するフォールバックコメントが返される
        assert fallback_comment == "爽やかな一日ですね"
    
    def test_get_fallback_comment_with_past_comments(self, test_state):
        """天気データなし、過去コメントありでのフォールバックテスト"""
        test_state.weather_data = None
        fallback_comment = _get_fallback_comment(test_state)
        
        # 過去コメントの最初のコメントが返される
        assert fallback_comment == "爽やかな朝です"
    
    def test_get_fallback_comment_default(self):
        """天気データも過去コメントもない場合のフォールバックテスト"""
        state = CommentGenerationState(
            location_name="テスト",
            target_datetime=datetime.now()
        )
        
        fallback_comment = _get_fallback_comment(state)
        
        # デフォルトコメントが返される
        assert fallback_comment == "今日も良い一日を"
    
    @patch('src.nodes.generate_comment_node.generate_comment_node')
    def test_generate_comment_with_fallback_success(self, mock_generate_node, test_state):
        """フォールバック機能付き生成の成功テスト"""
        # 最初の試行で成功するケース
        mock_generate_node.return_value = test_state
        test_state.generated_comment = "成功コメント"
        
        result_state = generate_comment_with_fallback(test_state)
        
        assert result_state.generated_comment == "成功コメント"
        mock_generate_node.assert_called_once()
    
    @patch('src.nodes.generate_comment_node.generate_comment_node')
    def test_generate_comment_with_fallback_retry(self, mock_generate_node, test_state):
        """フォールバック機能付き生成のリトライテスト"""
        # 最初の2回は失敗、3回目で成功
        mock_generate_node.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            test_state
        ]
        test_state.generated_comment = "最終成功コメント"
        
        result_state = generate_comment_with_fallback(test_state)
        
        assert result_state.generated_comment == "最終成功コメント"
        assert mock_generate_node.call_count == 3
    
    @patch('src.nodes.generate_comment_node.generate_comment_node')
    @patch('src.nodes.generate_comment_node._get_fallback_comment')
    def test_generate_comment_with_fallback_all_failed(self, mock_fallback, mock_generate_node, test_state):
        """全プロバイダー失敗時のテスト"""
        # 全プロバイダーで失敗
        mock_generate_node.side_effect = Exception("All failed")
        mock_fallback.return_value = "最終フォールバック"
        
        result_state = generate_comment_with_fallback(test_state)
        
        assert result_state.generated_comment == "最終フォールバック"
        assert result_state.generation_metadata['llm_provider'] == 'fallback_all_failed'
        assert result_state.generation_metadata['is_fallback'] is True


class TestGenerationResult:
    """GenerationResultのテスト"""
    
    def test_generation_result_creation(self):
        """GenerationResult作成テスト"""
        result = GenerationResult(
            generated_comment="テストコメント",
            provider_used="openai",
            generation_time_ms=1500
        )
        
        assert result.generated_comment == "テストコメント"
        assert result.provider_used == "openai"
        assert result.generation_time_ms == 1500
        assert result.is_fallback is False
        assert result.metadata == {}
    
    def test_generation_result_with_metadata(self):
        """メタデータ付きGenerationResult作成テスト"""
        metadata = {
            'prompt_length': 500,
            'generated_at': '2024-06-05T09:00:00'
        }
        
        result = GenerationResult(
            generated_comment="テストコメント",
            provider_used="gemini",
            generation_time_ms=2000,
            is_fallback=True,
            metadata=metadata
        )
        
        assert result.is_fallback is True
        assert result.metadata['prompt_length'] == 500
        assert result.metadata['generated_at'] == '2024-06-05T09:00:00'


class TestIntegration:
    """統合テスト"""
    
    @patch('src.nodes.generate_comment_node.LLMClientFactory')
    @patch('src.nodes.generate_comment_node.CommentPromptBuilder')
    def test_end_to_end_comment_generation(self, mock_prompt_builder, mock_client_factory, test_state):
        """エンドツーエンドのコメント生成テスト"""
        # モック設定
        mock_client = Mock()
        mock_client.generate_comment.return_value = "完璧な天気ですね"
        mock_client_factory.return_value.create_client.return_value = mock_client
        
        mock_builder = Mock()
        mock_builder.build_prompt.return_value = "詳細なプロンプト"
        mock_prompt_builder.return_value = mock_builder
        
        # 初期状態確認
        assert test_state.generated_comment is None
        assert 'llm_provider' not in test_state.generation_metadata
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 最終確認
        assert result_state.generated_comment == "完璧な天気ですね"
        assert result_state.location_name == "稚内"
        assert result_state.weather_data.weather_description == "晴れ"
        assert len(result_state.past_comments) == 2
        
        # メタデータ確認
        metadata = result_state.generation_metadata
        assert metadata['llm_provider'] == 'openai'
        assert 'generation_time_ms' in metadata
        assert 'generated_at' in metadata


if __name__ == '__main__':
    pytest.main([__file__])
