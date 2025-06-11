"""
コメントペア選択ノードのテスト
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment, CommentType
from src.data.weather_data import WeatherForecast
from src.nodes.select_comment_pair_node import (
    select_comment_pair_node,
    _select_best_comment_with_llm,
    _is_weather_matched,
    _generate_selection_prompt,
)


class TestSelectCommentPairNode:
    """SelectCommentPairNodeのテストスイート"""

    def setup_method(self):
        """テストセットアップ"""
        from src.data.weather_data import WeatherCondition, WindDirection
        
        self.sample_weather = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_condition=WeatherCondition.CLEAR,
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction=WindDirection.N,
            wind_direction_degrees=0,
        )

        self.sample_past_comments = [
            PastComment(
                comment_text="爽やかな朝ですね",
                comment_type=CommentType.WEATHER_COMMENT,
                location="東京",
                weather_condition="晴れ",
                temperature=19.0,
                datetime=datetime.now(),
            ),
            PastComment(
                comment_text="日焼け対策を忘れずに",
                comment_type=CommentType.ADVICE,
                location="東京",
                weather_condition="晴れ",
                temperature=21.0,
                datetime=datetime.now(),
            ),
            PastComment(
                comment_text="曇り空の一日です",
                comment_type=CommentType.WEATHER_COMMENT,
                location="東京",
                weather_condition="曇り",
                temperature=18.0,
                datetime=datetime.now(),
            ),
            PastComment(
                comment_text="傘があると安心です",
                comment_type=CommentType.ADVICE,
                location="東京",
                weather_condition="曇り",
                temperature=17.0,
                datetime=datetime.now(),
            ),
        ]

    @patch('src.llm.llm_manager.LLMManager')
    def test_select_comment_pair_node_success(self, mock_llm_manager):
        """正常系のテスト"""
        # LLMの応答をモック
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "0"  # 最初のコメントを選択
        mock_llm_manager.return_value = mock_llm
        
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.weather_data = self.sample_weather
        state.past_comments = self.sample_past_comments

        result = select_comment_pair_node(state)

        assert result.selected_pair is not None
        assert result.selected_pair.weather_comment is not None
        assert result.selected_pair.advice_comment is not None
        assert result.selected_pair.similarity_score == 1.0
        assert result.selected_pair.selection_reason == "LLMによる最適選択"

    def test_select_comment_pair_node_no_weather_data(self):
        """天気データがない場合"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.past_comments = self.sample_past_comments

        with pytest.raises(ValueError, match="天気データが利用できません"):
            select_comment_pair_node(state)

    def test_select_comment_pair_node_no_past_comments(self):
        """過去コメントがない場合"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.weather_data = self.sample_weather
        state.past_comments = []

        with pytest.raises(ValueError, match="過去コメントが存在しません"):
            select_comment_pair_node(state)

    def test_select_comment_pair_node_insufficient_comment_types(self):
        """コメントタイプが不足している場合"""
        state = CommentGenerationState(
            location_name="東京",
            target_datetime=datetime.now()
        )
        state.weather_data = self.sample_weather
        # weather_commentのみ
        state.past_comments = [
            comment for comment in self.sample_past_comments
            if comment.comment_type == CommentType.WEATHER_COMMENT
        ]

        with pytest.raises(ValueError, match="適切なコメントタイプが見つかりません"):
            select_comment_pair_node(state)

    @patch('src.llm.llm_manager.LLMManager')
    def test_select_best_comment_with_llm(self, mock_llm_manager):
        """LLMによるコメント選択のテスト"""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "1"
        mock_llm_manager.return_value = mock_llm
        
        weather_comments = [
            c for c in self.sample_past_comments if c.comment_type == CommentType.WEATHER_COMMENT
        ]
        
        result = _select_best_comment_with_llm(
            weather_comments,
            self.sample_weather,
            "東京",
            datetime.now(),
            mock_llm,
            CommentType.WEATHER_COMMENT
        )
        
        assert result == weather_comments[1]
        
    def test_is_weather_matched(self):
        """天気条件マッチングのテスト"""
        assert _is_weather_matched("晴れ", "晴れ") == True
        assert _is_weather_matched("晴れ時々曇り", "晴れ") == True
        assert _is_weather_matched("晴れ", "晴れ時々曇り") == True
        assert _is_weather_matched("雨", "晴れ") == False
        assert _is_weather_matched(None, "晴れ") == False
        assert _is_weather_matched("晴れ", "") == False
        
    def test_generate_selection_prompt(self):
        """プロンプト生成のテスト"""
        candidates = [
            {
                "index": 0,
                "text": "テストコメント",
                "weather": "晴れ",
                "temperature": 20.0,
                "season": "春",
            }
        ]
        
        prompt = _generate_selection_prompt(
            candidates,
            self.sample_weather,
            "東京",
            datetime.now(),
            CommentType.WEATHER_COMMENT
        )
        
        assert "東京" in prompt
        assert "晴れ" in prompt
        assert "20" in prompt
        assert "weather_comment" in prompt
        assert "選択基準" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
