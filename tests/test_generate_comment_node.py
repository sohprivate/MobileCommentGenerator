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
    _get_ng_words,
    _get_time_period,
    _get_season,
    _get_fallback_comment
)
from src.data.comment_generation_state import CommentGenerationState, create_test_state
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair


@pytest.fixture
def mock_weather_data():
    """モック天気データ"""
    weather_data = Mock(spec=WeatherForecast)
    weather_data.weather_description = "晴れ"
    weather_data.temperature = 20.5
    weather_data.humidity = 60
    weather_data.wind_speed = 2.5
    return weather_data


@pytest.fixture
def mock_comment_pair():
    """モックコメントペア"""
    weather_comment = Mock()
    weather_comment.comment_text = "爽やかな朝です"
    weather_comment.comment_type = "weather_comment"
    weather_comment.temperature = 20.0
    weather_comment.weather_condition = "晴れ"
    weather_comment.to_dict = Mock(return_value={"text": "爽やかな朝です"})
    
    advice_comment = Mock()
    advice_comment.comment_text = "日焼け対策を"
    advice_comment.comment_type = "advice"
    advice_comment.temperature = 20.0
    advice_comment.weather_condition = "晴れ"
    advice_comment.to_dict = Mock(return_value={"text": "日焼け対策を"})
    
    return CommentPair(
        weather_comment=weather_comment,
        advice_comment=advice_comment,
        similarity_score=0.85,
        selection_reason="天気条件が類似"
    )


@pytest.fixture
def test_state(mock_weather_data, mock_comment_pair):
    """テスト用状態"""
    state = {
        "location_name": "稚内",
        "target_datetime": datetime(2024, 6, 5, 9, 0, 0),
        "weather_data": mock_weather_data,
        "selected_pair": mock_comment_pair,
        "llm_provider": "openai"
    }
    return state


class TestGenerateCommentNode:
    """GenerateCommentNodeのテスト"""
    
    @patch('src.nodes.generate_comment_node.LLMManager')
    def test_generate_comment_node_success(self, mock_llm_manager_class, test_state):
        """正常なコメント生成のテスト"""
        # モック設定
        mock_manager = Mock()
        mock_manager.generate_comment.return_value = "爽やかな朝ですね"
        mock_llm_manager_class.return_value = mock_manager
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 検証
        assert result_state["generated_comment"] == "爽やかな朝ですね"
        assert "generation_metadata" in result_state
        assert result_state["generation_metadata"]["llm_provider"] == "openai"
        assert "generation_timestamp" in result_state["generation_metadata"]
        assert "constraints_applied" in result_state["generation_metadata"]
        
        # モック呼び出し確認
        mock_llm_manager_class.assert_called_once_with(provider="openai")
        mock_manager.generate_comment.assert_called_once()
        
        # 制約条件の確認
        call_args = mock_manager.generate_comment.call_args
        constraints = call_args.kwargs["constraints"]
        assert constraints["max_length"] == 15
        assert constraints["time_period"] == "朝"
        assert constraints["season"] == "夏"
    
    @patch('src.nodes.generate_comment_node.LLMManager')
    def test_generate_comment_node_no_weather_data(self, mock_llm_manager_class):
        """天気データなしの場合のエラーテスト"""
        # モックコメントペアを作成
        weather_comment = Mock()
        weather_comment.comment_type = "weather_comment"
        advice_comment = Mock()
        advice_comment.comment_type = "advice"
        
        state = {
            "location_name": "稚内",
            "target_datetime": datetime.now(),
            "selected_pair": CommentPair(
                weather_comment=weather_comment,
                advice_comment=advice_comment,
                similarity_score=0.5,
                selection_reason="test"
            )
        }
        
        # テスト実行
        result_state = generate_comment_node(state)
        
        # エラーが記録され、フォールバックコメントが設定される
        assert "errors" in result_state
        assert len(result_state["errors"]) > 0
        assert result_state["errors"][0]["node"] == "generate_comment"
        assert "Weather data is required" in result_state["errors"][0]["error"]
        assert result_state["generated_comment"] == "今日も一日頑張ろう"  # フォールバック
    
    @patch('src.nodes.generate_comment_node.LLMManager')
    def test_generate_comment_node_no_selected_pair(self, mock_llm_manager_class, mock_weather_data):
        """選択ペアなしの場合のエラーテスト"""
        state = {
            "location_name": "稚内",
            "target_datetime": datetime.now(),
            "weather_data": mock_weather_data
        }
        
        # テスト実行
        result_state = generate_comment_node(state)
        
        # エラーが記録され、フォールバックコメントが設定される
        assert "errors" in result_state
        assert "Selected comment pair is required" in result_state["errors"][0]["error"]
        assert result_state["generated_comment"] == "晴れて気持ちいい"  # 天気ベースのフォールバック
    
    @patch('src.nodes.generate_comment_node.LLMManager')
    def test_generate_comment_node_llm_error(self, mock_llm_manager_class, test_state):
        """LLM生成エラー時のフォールバック処理テスト"""
        # モック設定（例外発生）
        mock_manager = Mock()
        mock_manager.generate_comment.side_effect = Exception("API Error")
        mock_llm_manager_class.return_value = mock_manager
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 検証
        assert result_state["generated_comment"] == "晴れて気持ちいい"  # フォールバック
        assert "errors" in result_state
        assert "API Error" in result_state["errors"][0]["error"]
    
    def test_get_ng_words(self):
        """NGワードリスト取得のテスト"""
        ng_words = _get_ng_words()
        
        assert isinstance(ng_words, list)
        assert "災害" in ng_words
        assert "危険" in ng_words
        assert "絶対" in ng_words
    
    def test_get_time_period(self):
        """時間帯判定のテスト"""
        # 朝
        assert _get_time_period(datetime(2024, 6, 5, 7, 0)) == "朝"
        # 昼
        assert _get_time_period(datetime(2024, 6, 5, 14, 0)) == "昼"
        # 夕方
        assert _get_time_period(datetime(2024, 6, 5, 18, 0)) == "夕方"
        # 夜
        assert _get_time_period(datetime(2024, 6, 5, 22, 0)) == "夜"
        # None の場合は現在時刻で判定
        assert _get_time_period(None) in ["朝", "昼", "夕方", "夜"]
    
    def test_get_season(self):
        """季節判定のテスト"""
        # 春
        assert _get_season(datetime(2024, 4, 1)) == "春"
        # 夏
        assert _get_season(datetime(2024, 7, 1)) == "夏"
        # 秋
        assert _get_season(datetime(2024, 10, 1)) == "秋"
        # 冬
        assert _get_season(datetime(2024, 1, 1)) == "冬"
        # None の場合は現在時刻で判定
        assert _get_season(None) in ["春", "夏", "秋", "冬"]
    
    def test_get_fallback_comment_with_weather(self, mock_weather_data):
        """天気データありでのフォールバックコメントテスト"""
        fallback_comment = _get_fallback_comment(mock_weather_data)
        
        # 晴れの天気データがあるので、対応するフォールバックコメントが返される
        assert fallback_comment == "晴れて気持ちいい"
    
    def test_get_fallback_comment_rain(self):
        """雨天時のフォールバックコメントテスト"""
        weather_data = Mock(spec=WeatherForecast)
        weather_data.weather_description = "雨"
        
        fallback_comment = _get_fallback_comment(weather_data)
        assert fallback_comment == "傘をお忘れなく"
    
    def test_get_fallback_comment_default(self):
        """天気データなしの場合のフォールバックテスト"""
        fallback_comment = _get_fallback_comment(None)
        
        # デフォルトコメントが返される
        assert fallback_comment == "今日も一日頑張ろう"
    
    def test_get_fallback_comment_unknown_weather(self):
        """未知の天気の場合のフォールバックテスト"""
        weather_data = Mock(spec=WeatherForecast)
        weather_data.weather_description = "霧"
        
        fallback_comment = _get_fallback_comment(weather_data)
        
        # デフォルトコメントが返される
        assert fallback_comment == "今日も良い一日を"


class TestIntegration:
    """統合テスト"""
    
    @patch('src.nodes.generate_comment_node.LLMManager')
    def test_end_to_end_comment_generation(self, mock_llm_manager_class, test_state):
        """エンドツーエンドのコメント生成テスト"""
        # モック設定
        mock_manager = Mock()
        mock_manager.generate_comment.return_value = "完璧な天気ですね"
        mock_llm_manager_class.return_value = mock_manager
        
        # 初期状態確認
        assert "generated_comment" not in test_state
        
        # テスト実行
        result_state = generate_comment_node(test_state)
        
        # 最終確認
        assert result_state["generated_comment"] == "完璧な天気ですね"
        assert result_state["location_name"] == "稚内"
        assert result_state["weather_data"].weather_description == "晴れ"
        
        # メタデータ確認
        metadata = result_state["generation_metadata"]
        assert metadata["llm_provider"] == "openai"
        assert "generation_timestamp" in metadata
        assert metadata["constraints_applied"]["max_length"] == 15
        assert metadata["constraints_applied"]["time_period"] == "朝"
        assert metadata["constraints_applied"]["season"] == "夏"


if __name__ == '__main__':
    pytest.main([__file__])