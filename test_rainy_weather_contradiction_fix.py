#!/usr/bin/env python3
"""雨天時の「梅雨の中休み」問題修正のテスト"""

import sys
import os
from datetime import datetime

# プロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.nodes.select_comment_pair_node import _should_exclude_weather_comment, _should_exclude_comment_combination
from src.data.comment_pair import CommentPair

def test_rainy_weather_contradictions():
    """雨天時の矛盾表現テスト"""
    print("🚨 雨天時の矛盾表現テストを開始")
    
    # 雨天時の天気データを作成
    weather_data = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=20.0,
        weather_code="rain",
        weather_condition=WeatherCondition.RAIN,
        weather_description="雨",
        precipitation=1.0,  # 降水量1mm
        humidity=80,
        wind_speed=3.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    validator = WeatherCommentValidator()
    
    # テストケース: 問題となった「梅雨の中休み」コメント
    test_comments = [
        # 雨天時に不適切なコメント
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="梅雨の中休みで過ごしやすい一日になりそうです",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "梅雨"}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="晴れ間が見える穏やかな天気です",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "梅雨"}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="一時的な晴れで快適な体感です",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "梅雨"}
        ),
        # 雨天時に適切なコメント
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="本格的な雨に注意が必要です",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "梅雨"}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="雨が降り続く一日となりそうです",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "梅雨"}
        )
    ]
    
    print(f"天気条件: {weather_data.weather_description}, 降水量: {weather_data.precipitation}mm")
    print("\n--- バリデーションテスト ---")
    
    for comment in test_comments:
        is_valid, reason = validator.validate_comment(comment, weather_data)
        status = "✅ 適切" if is_valid else "❌ 不適切"
        print(f"{status}: '{comment.comment_text}' - {reason}")
    
    print("\n--- フィルタリングテスト ---")
    
    # select_comment_pair_nodeの除外関数もテスト
    for comment in test_comments:
        should_exclude = _should_exclude_weather_comment(comment.comment_text, weather_data)
        status = "❌ 除外" if should_exclude else "✅ 通過"
        print(f"{status}: '{comment.comment_text}'")
    
    print("\n--- 組み合わせテスト ---")
    
    # 雨天時の不適切な組み合わせをテスト
    inappropriate_weather = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="雨",
        comment_text="梅雨の中休みで穏やかな空です",
        comment_type=CommentType.WEATHER_COMMENT,
        raw_data={"season": "梅雨"}
    )
    
    inappropriate_advice = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="雨",
        comment_text="過ごしやすい体感でお出かけ日和です",
        comment_type=CommentType.ADVICE,
        raw_data={"season": "梅雨"}
    )
    
    bad_pair = CommentPair(
        weather_comment=inappropriate_weather,
        advice_comment=inappropriate_advice,
        similarity_score=1.0,
        selection_reason="テスト用"
    )
    
    should_exclude_pair = _should_exclude_comment_combination(bad_pair, weather_data)
    print(f"不適切組み合わせ {'❌ 除外される' if should_exclude_pair else '✅ 通過する'}")
    print(f"  天気: '{inappropriate_weather.comment_text}'")
    print(f"  アドバイス: '{inappropriate_advice.comment_text}'")
    
    print("\n--- フィルタリング結果 ---")
    
    # 適切なコメントのみ残るかテスト
    filtered_comments = validator.filter_comments(test_comments, weather_data)
    print(f"元の件数: {len(test_comments)}, フィルタリング後: {len(filtered_comments)}")
    
    for comment in filtered_comments:
        print(f"✅ 残存: '{comment.comment_text}'")

def test_other_weather_conditions():
    """他の天気条件でのテスト"""
    print("\n🌤️ 他の天気条件でのテスト")
    
    # 晴天時
    sunny_weather = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=25.0,
        weather_code="clear",
        weather_condition=WeatherCondition.CLEAR,
        weather_description="晴れ",
        precipitation=0.0,
        humidity=50,
        wind_speed=2.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    # 晴天時には「梅雨の中休み」は適切
    sunny_comment = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="晴れ",
        comment_text="梅雨の中休みで過ごしやすい一日です",
        comment_type=CommentType.WEATHER_COMMENT,
        raw_data={"season": "梅雨"}
    )
    
    validator = WeatherCommentValidator()
    is_valid, reason = validator.validate_comment(sunny_comment, sunny_weather)
    print(f"晴天時の '梅雨の中休み': {'✅ 適切' if is_valid else '❌ 不適切'} - {reason}")

if __name__ == "__main__":
    test_rainy_weather_contradictions()
    test_other_weather_conditions()
    print("\n🎉 テスト完了")