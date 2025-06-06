"""
コメントペア選択ノードのテスト
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.data.comment_generation_state import CommentGenerationState
from src.data.past_comment import PastComment
from src.data.weather_data import WeatherForecast
from src.nodes.select_comment_pair_node import (
    select_comment_pair_node,
    _generate_candidates,
    _select_best_pair,
    _create_default_pair
)
from src.algorithms.similarity_calculator import CommentSimilarityCalculator


class TestSelectCommentPairNode:
    """SelectCommentPairNodeのテストスイート"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.sample_weather = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction="北"
        )
        
        self.sample_past_comments = [
            PastComment(
                comment_text="爽やかな朝ですね",
                comment_type="weather_comment",
                location="東京",
                weather_condition="晴れ",
                temperature=19.0,
                datetime=datetime.now()
            ),
            PastComment(
                comment_text="日焼け対策を忘れずに",
                comment_type="advice",
                location="東京",
                weather_condition="晴れ",
                temperature=21.0,
                datetime=datetime.now()
            ),
            PastComment(
                comment_text="曇り空の一日です",
                comment_type="weather_comment",
                location="東京",
                weather_condition="曇り",
                temperature=18.0,
                datetime=datetime.now()
            ),
            PastComment(
                comment_text="傘があると安心です",
                comment_type="advice",
                location="東京",
                weather_condition="曇り",
                temperature=17.0,
                datetime=datetime.now()
            )
        ]
    
    def test_select_comment_pair_node_success(self):
        """正常系のテスト"""
        state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "weather_data": self.sample_weather.to_dict(),
            "past_comments": [comment.to_dict() for comment in self.sample_past_comments]
        }
        
        result = select_comment_pair_node(state)
        
        assert "selected_pair" in result
        assert result["selected_pair"] is not None
        assert "weather_comment" in result["selected_pair"]
        assert "advice_comment" in result["selected_pair"]
        assert "similarity_score" in result["selected_pair"]
        assert "selection_reason" in result["selected_pair"]
    
    def test_select_comment_pair_node_no_weather_data(self):
        """天気データがない場合"""
        state = {
            "location_name": "東京",
            "past_comments": [comment.to_dict() for comment in self.sample_past_comments]
        }
        
        result = select_comment_pair_node(state)
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert "selected_pair" in result
    
    def test_select_comment_pair_node_no_past_comments(self):
        """過去コメントがない場合"""
        state = {
            "location_name": "東京",
            "weather_data": self.sample_weather.to_dict(),
            "past_comments": []
        }
        
        result = select_comment_pair_node(state)
        
        assert "selected_pair" in result
        assert result["selected_pair"]["selection_reason"] == "デフォルトペア（過去データなし）"
    
    def test_select_comment_pair_node_insufficient_comment_types(self):
        """コメントタイプが不足している場合"""
        # weather_commentのみ
        state = {
            "location_name": "東京",
            "weather_data": self.sample_weather.to_dict(),
            "past_comments": [
                comment.to_dict() for comment in self.sample_past_comments
                if comment.comment_type == "weather_comment"
            ]
        }
        
        result = select_comment_pair_node(state)
        
        assert "selected_pair" in result
        assert result["selected_pair"]["selection_reason"] == "デフォルトペア（過去データなし）"
    
    def test_generate_candidates(self):
        """候補生成のテスト"""
        weather_comments = [c for c in self.sample_past_comments if c.comment_type == "weather_comment"]
        advice_comments = [c for c in self.sample_past_comments if c.comment_type == "advice"]
        calculator = CommentSimilarityCalculator()
        
        candidates = _generate_candidates(
            weather_comments,
            advice_comments,
            self.sample_weather,
            "東京",
            datetime.now(),
            calculator
        )
        
        assert len(candidates) > 0
        assert all(c.total_score >= 0.3 for c in candidates)
    
    def test_select_best_pair(self):
        """最適ペア選択のテスト"""
        from src.data.comment_pair import CommentPairCandidate
        
        candidates = [
            CommentPairCandidate(
                weather_comment=self.sample_past_comments[0],
                advice_comment=self.sample_past_comments[1],
                weather_similarity=0.9,
                semantic_similarity=0.8,
                temporal_similarity=0.7,
                location_similarity=1.0
            ),
            CommentPairCandidate(
                weather_comment=self.sample_past_comments[2],
                advice_comment=self.sample_past_comments[3],
                weather_similarity=0.5,
                semantic_similarity=0.4,
                temporal_similarity=0.6,
                location_similarity=1.0
            )
        ]
        
        best_pair = _select_best_pair(candidates)
        
        assert best_pair is not None
        assert best_pair.similarity_score == candidates[0].total_score
        assert best_pair.weather_comment == candidates[0].weather_comment
        assert best_pair.advice_comment == candidates[0].advice_comment
    
    def test_create_default_pair(self):
        """デフォルトペア作成のテスト"""
        # 天気データあり
        default_pair = _create_default_pair(self.sample_weather)
        
        assert default_pair is not None
        assert default_pair["weather_comment"]["comment_text"] == "いい天気ですね"
        assert default_pair["advice_comment"]["comment_text"] == "日差しにご注意を"
        assert default_pair["selection_reason"] == "デフォルトペア（過去データなし）"
        
        # 天気データなし
        default_pair_no_weather = _create_default_pair(None)
        
        assert default_pair_no_weather is not None
        assert default_pair_no_weather["weather_comment"]["comment_text"] == "曇り空ですね"


class TestCommentSimilarityCalculator:
    """類似度計算器のテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.calculator = CommentSimilarityCalculator()
        self.sample_weather = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction="北"
        )
    
    def test_weather_similarity(self):
        """天気条件類似度のテスト"""
        # 同じ天気
        comment1 = PastComment(
            comment_text="test",
            comment_type="weather_comment",
            weather_condition="晴れ"
        )
        score1 = self.calculator.calculate_weather_similarity(self.sample_weather, comment1)
        assert score1 == 1.0
        
        # 類似天気
        comment2 = PastComment(
            comment_text="test",
            comment_type="weather_comment",
            weather_condition="曇り"
        )
        score2 = self.calculator.calculate_weather_similarity(self.sample_weather, comment2)
        assert score2 == 0.5
    
    def test_temperature_similarity(self):
        """気温類似度のテスト"""
        # 同じ気温
        score1 = self.calculator.calculate_temperature_similarity(20.0, 20.0)
        assert score1 == 1.0
        
        # 5度差
        score2 = self.calculator.calculate_temperature_similarity(20.0, 25.0)
        assert score2 == 0.5
        
        # 10度以上差
        score3 = self.calculator.calculate_temperature_similarity(20.0, 35.0)
        assert score3 == 0.0
        
        # データなし
        score4 = self.calculator.calculate_temperature_similarity(20.0, None)
        assert score4 == 0.5
    
    def test_location_similarity(self):
        """地点類似度のテスト"""
        # 完全一致
        score1 = self.calculator.calculate_location_similarity("東京", "東京")
        assert score1 == 1.0
        
        # 異なる地点
        score2 = self.calculator.calculate_location_similarity("東京", "大阪")
        assert score2 < 1.0
    
    def test_temporal_similarity(self):
        """時間的類似度のテスト"""
        now = datetime.now()
        
        # 同じ時間
        score1 = self.calculator.calculate_temporal_similarity(now, now)
        assert score1 == 1.0
        
        # 3時間差
        three_hours_ago = datetime(now.year, now.month, now.day, now.hour - 3, now.minute)
        score2 = self.calculator.calculate_temporal_similarity(now, three_hours_ago)
        assert score2 == 0.7
    
    def test_composite_similarity(self):
        """総合類似度のテスト"""
        comment = PastComment(
            comment_text="爽やかな晴れの日です",
            comment_type="weather_comment",
            location="東京",
            weather_condition="晴れ",
            temperature=19.0,
            datetime=datetime.now()
        )
        
        scores = self.calculator.calculate_composite_similarity(
            self.sample_weather,
            comment,
            datetime.now(),
            "東京"
        )
        
        assert "weather_similarity" in scores
        assert "temperature_similarity" in scores
        assert "semantic_similarity" in scores
        assert "temporal_similarity" in scores
        assert "location_similarity" in scores
        assert "total_score" in scores
        assert 0.0 <= scores["total_score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
