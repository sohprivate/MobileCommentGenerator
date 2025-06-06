"""
過去コメントデータクラスのテスト
"""

import pytest
from datetime import datetime
from src.data.past_comment import (
    PastComment, 
    PastCommentCollection,
    CommentType
)


class TestPastComment:
    """PastComment クラスのテスト"""
    
    def test_valid_past_comment_creation(self):
        """正常な過去コメントデータの作成テスト"""
        comment = PastComment(
            location="東京",
            datetime=datetime(2024, 6, 5, 12, 0),
            weather_condition="晴れ",
            comment_text="爽やかな朝ですね",
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=22.5,
            weather_code="100"
        )
        
        assert comment.location == "東京"
        assert comment.comment_text == "爽やかな朝ですね"
        assert comment.comment_type == CommentType.WEATHER_COMMENT
        assert comment.temperature == 22.5
        assert comment.get_character_count() == 8
        assert comment.is_within_length_limit()
    
    def test_invalid_empty_comment(self):
        """空コメントのテスト"""
        with pytest.raises(ValueError, match="コメント本文が空です"):
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="",  # 空文字
                comment_type=CommentType.WEATHER_COMMENT
            )
    
    def test_invalid_empty_location(self):
        """空地点名のテスト"""
        with pytest.raises(ValueError, match="地点名が空です"):
            PastComment(
                location="",  # 空文字
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="テストコメント",
                comment_type=CommentType.WEATHER_COMMENT
            )
    
    def test_invalid_temperature(self):
        """異常な気温値のテスト"""
        with pytest.raises(ValueError, match="異常な気温値"):
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="テストコメント",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=-100.0  # 異常値
            )
    
    def test_weather_condition_matching(self):
        """天気状況マッチングのテスト"""
        comment = PastComment(
            location="大阪",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="良い天気",
            comment_type=CommentType.WEATHER_COMMENT
        )
        
        # 完全一致
        assert comment.matches_weather_condition("晴れ", fuzzy=False)
        assert not comment.matches_weather_condition("曇り", fuzzy=False)
        
        # あいまい検索
        assert comment.matches_weather_condition("快晴", fuzzy=True)
        assert comment.matches_weather_condition("sunny", fuzzy=True)
    
    def test_similarity_calculation(self):
        """類似度計算のテスト"""
        comment = PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="晴れ",
            comment_text="暖かい日です",
            comment_type=CommentType.WEATHER_COMMENT,
            temperature=20.0
        )
        
        # 同じ条件での類似度
        score1 = comment.calculate_similarity_score("晴れ", 20.0, "東京")
        assert score1 == 1.0  # 完全一致
        
        # 部分的一致
        score2 = comment.calculate_similarity_score("晴れ", 25.0, "大阪")
        assert 0.5 < score2 < 1.0  # 天気は一致、気温と地点が異なる
        
        # 一致しない条件
        score3 = comment.calculate_similarity_score("雨", 5.0, "札幌")
        assert score3 < 0.5
    
    def test_to_dict_conversion(self):
        """辞書変換のテスト"""
        comment = PastComment(
            location="福岡",
            datetime=datetime(2024, 6, 5, 15, 0),
            weather_condition="曇り",
            comment_text="少し肌寒いです",
            comment_type=CommentType.ADVICE,
            temperature=18.0
        )
        
        comment_dict = comment.to_dict()
        
        assert comment_dict['location'] == "福岡"
        assert comment_dict['comment_text'] == "少し肌寒いです"
        assert comment_dict['comment_type'] == 'advice'
        assert comment_dict['temperature'] == 18.0
    
    def test_from_dict_creation(self):
        """辞書からの生成テスト"""
        data = {
            'location': '札幌',
            'datetime': '2024-06-05T09:00:00+09:00',
            'weather_condition': '雪',
            'comment_text': '防寒対策必須',
            'comment_type': 'advice',
            'temperature': -2.0
        }
        
        comment = PastComment.from_dict(data)
        
        assert comment.location == '札幌'
        assert comment.weather_condition == '雪'
        assert comment.comment_type == CommentType.ADVICE
        assert comment.temperature == -2.0


class TestPastCommentCollection:
    """PastCommentCollection クラスのテスト"""
    
    def test_collection_creation(self):
        """コレクション作成のテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime(2024, 6, 5, 12, 0),
                weather_condition="晴れ",
                comment_text="良い天気",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime(2024, 6, 5, 12, 0),
                weather_condition="晴れ",
                comment_text="日焼け注意",
                comment_type=CommentType.ADVICE
            )
        ]
        
        collection = PastCommentCollection(
            comments=comments,
            source_period="202406"
        )
        
        assert len(collection.comments) == 2
        assert collection.source_period == "202406"
    
    def test_filter_by_location(self):
        """地点フィルタリングのテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="東京は晴れ",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="曇り",
                comment_text="大阪は曇り",
                comment_type=CommentType.WEATHER_COMMENT
            )
        ]
        
        collection = PastCommentCollection(comments=comments)
        
        # 完全一致フィルタ
        tokyo_comments = collection.filter_by_location("東京", exact_match=True)
        assert len(tokyo_comments.comments) == 1
        assert tokyo_comments.comments[0].location == "東京"
        
        # 部分一致フィルタ
        east_comments = collection.filter_by_location("東", exact_match=False)
        assert len(east_comments.comments) == 1
    
    def test_filter_by_weather_condition(self):
        """天気状況フィルタリングのテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="晴天です",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="快晴",
                comment_text="快晴です",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="福岡",
                datetime=datetime.now(),
                weather_condition="雨",
                comment_text="雨です",
                comment_type=CommentType.WEATHER_COMMENT
            )
        ]
        
        collection = PastCommentCollection(comments=comments)
        
        # あいまい検索（"晴れ"で"快晴"も含む）
        sunny_comments = collection.filter_by_weather_condition("晴れ", fuzzy=True)
        assert len(sunny_comments.comments) == 2
        
        # 完全一致
        exact_sunny = collection.filter_by_weather_condition("晴れ", fuzzy=False)
        assert len(exact_sunny.comments) == 1
    
    def test_filter_by_comment_type(self):
        """コメントタイプフィルタリングのテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="良い天気",
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="水分補給を",
                comment_type=CommentType.ADVICE
            )
        ]
        
        collection = PastCommentCollection(comments=comments)
        
        # 天気コメントのみ
        weather_comments = collection.filter_by_comment_type(CommentType.WEATHER_COMMENT)
        assert len(weather_comments.comments) == 1
        assert weather_comments.comments[0].comment_text == "良い天気"
        
        # アドバイスのみ
        advice_comments = collection.filter_by_comment_type(CommentType.ADVICE)
        assert len(advice_comments.comments) == 1
        assert advice_comments.comments[0].comment_text == "水分補給を"
    
    def test_get_similar_comments(self):
        """類似コメント取得のテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="暖かい",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=25.0
            ),
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="暑い",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=30.0
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="雨",
                comment_text="濡れる",
                comment_type=CommentType.WEATHER_COMMENT,
                temperature=20.0
            )
        ]
        
        collection = PastCommentCollection(comments=comments)
        
        # 晴れ、27度、東京に類似するコメント
        similar = collection.get_similar_comments(
            target_weather_condition="晴れ",
            target_temperature=27.0,
            target_location="東京",
            min_similarity=0.5,
            max_results=5
        )
        
        # 2つの晴れコメントが類似として取得される
        assert len(similar) == 2
        # 類似度でソートされている（30度より25度の方が27度に近い）
        assert similar[0].temperature == 25.0
        assert similar[1].temperature == 30.0
    
    def test_get_statistics(self):
        """統計情報取得のテスト"""
        comments = [
            PastComment(
                location="東京",
                datetime=datetime.now(),
                weather_condition="晴れ",
                comment_text="短い",  # 3文字
                comment_type=CommentType.WEATHER_COMMENT
            ),
            PastComment(
                location="大阪",
                datetime=datetime.now(),
                weather_condition="曇り",
                comment_text="これは少し長めのコメントです",  # 15文字
                comment_type=CommentType.ADVICE
            )
        ]
        
        collection = PastCommentCollection(comments=comments)
        stats = collection.get_statistics()
        
        assert stats['total_comments'] == 2
        assert stats['type_distribution']['weather_comment'] == 1
        assert stats['type_distribution']['advice'] == 1
        assert stats['character_stats']['min_length'] == 3
        assert stats['character_stats']['max_length'] == 15
        assert stats['character_stats']['within_15_chars'] == 2


class TestCommentType:
    """CommentType 列挙型のテスト"""
    
    def test_comment_type_values(self):
        """コメントタイプの値テスト"""
        assert CommentType.WEATHER_COMMENT.value == "weather_comment"
        assert CommentType.ADVICE.value == "advice"
        assert CommentType.UNKNOWN.value == "unknown"


if __name__ == "__main__":
    pytest.main([__file__])
