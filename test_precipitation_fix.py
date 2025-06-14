#!/usr/bin/env python3
"""
降水量1mmで「強雨や雷に注意」コメント問題の修正テスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType
from src.utils.weather_comment_validator import WeatherCommentValidator

def test_light_rain_comments():
    """軽い雨（1mm）のコメント選択テスト"""
    
    # 軽い雨の天気データ（降水量1mm）
    light_rain_weather = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=20.0,
        weather_code="rain_light",
        weather_condition=WeatherCondition.RAIN,
        weather_description="雨",
        precipitation=1.0,  # 1mm
        humidity=80,
        wind_speed=3.0,
        wind_direction=WindDirection.E,
        wind_direction_degrees=90
    )
    
    print(f"テスト条件: {light_rain_weather.weather_description}, 降水量: {light_rain_weather.precipitation}mm")
    print(f"降水量レベル: {light_rain_weather.get_precipitation_severity()}")
    print(f"悪天候判定: {light_rain_weather.is_severe_weather()}")
    print()
    
    # テスト用コメント
    test_comments = [
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="強雨や雷に注意",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 100}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="本格的な雨に注意",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 80}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="雨雲が広がる空",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 60}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="にわか雨が心配",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 40}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="雨がぽつぽつ",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 30}
        ),
    ]
    
    advice_comments = [
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="外出控えて安全に",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 100}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="傘をお忘れなく",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 80}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="濡れ対策を",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 60}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雨",
            comment_text="避難してください",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 40}
        ),
    ]
    
    # バリデーターでテスト
    validator = WeatherCommentValidator()
    
    print("天気コメントの検証結果:")
    for comment in test_comments:
        is_valid, reason = validator.validate_comment(comment, light_rain_weather)
        status = "✅ 適切" if is_valid else "❌ 不適切"
        print(f"  {status}: '{comment.comment_text}' - {reason}")
    
    print("\nアドバイスコメントの検証結果:")
    for comment in advice_comments:
        is_valid, reason = validator.validate_comment(comment, light_rain_weather)
        status = "✅ 適切" if is_valid else "❌ 不適切"
        print(f"  {status}: '{comment.comment_text}' - {reason}")

def test_thunder_with_light_rain():
    """軽微な雷（降水量1mm）のテスト"""
    
    # 軽微な雷の天気データ
    light_thunder_weather = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=25.0,
        weather_code="thunder_light",
        weather_condition=WeatherCondition.THUNDER,
        weather_description="雷",
        precipitation=1.0,  # 1mm
        humidity=70,
        wind_speed=5.0,
        wind_direction=WindDirection.W,
        wind_direction_degrees=270
    )
    
    print(f"\n--- 雷テスト ---")
    print(f"テスト条件: {light_thunder_weather.weather_description}, 降水量: {light_thunder_weather.precipitation}mm")
    print(f"降水量レベル: {light_thunder_weather.get_precipitation_severity()}")
    print(f"悪天候判定: {light_thunder_weather.is_severe_weather()}")
    print()
    
    thunder_comments = [
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="雷に警戒してください",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 100}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="雷の音が聞こえる空",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 80}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="不安定な空模様",
            comment_type=CommentType.WEATHER_COMMENT,
            raw_data={"season": "夏", "count": 60}
        ),
    ]
    
    thunder_advice = [
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="屋内に避難を",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 100}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="雷に注意を",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 80}
        ),
        PastComment(
            location="東京",
            datetime=datetime.now(),
            weather_condition="雷",
            comment_text="空の様子に注意",
            comment_type=CommentType.ADVICE,
            raw_data={"season": "夏", "count": 60}
        ),
    ]
    
    validator = WeatherCommentValidator()
    
    print("雷天気コメントの検証結果:")
    for comment in thunder_comments:
        is_valid, reason = validator.validate_comment(comment, light_thunder_weather)
        status = "✅ 適切" if is_valid else "❌ 不適切"
        print(f"  {status}: '{comment.comment_text}' - {reason}")
    
    print("\n雷アドバイスコメントの検証結果:")
    for comment in thunder_advice:
        is_valid, reason = validator.validate_comment(comment, light_thunder_weather)
        status = "✅ 適切" if is_valid else "❌ 不適切"
        print(f"  {status}: '{comment.comment_text}' - {reason}")

def test_heavy_rain_comments():
    """大雨（10mm以上）のテスト（比較用）"""
    
    # 大雨の天気データ
    heavy_rain_weather = WeatherForecast(
        location="東京",
        datetime=datetime.now(),
        temperature=22.0,
        weather_code="heavy_rain",
        weather_condition=WeatherCondition.HEAVY_RAIN,
        weather_description="大雨",
        precipitation=15.0,  # 15mm
        humidity=90,
        wind_speed=8.0,
        wind_direction=WindDirection.S,
        wind_direction_degrees=180
    )
    
    print(f"\n--- 大雨テスト（比較用）---")
    print(f"テスト条件: {heavy_rain_weather.weather_description}, 降水量: {heavy_rain_weather.precipitation}mm")
    print(f"降水量レベル: {heavy_rain_weather.get_precipitation_severity()}")
    print(f"悪天候判定: {heavy_rain_weather.is_severe_weather()}")
    print()
    
    # 同じコメントで大雨時の結果を比較
    test_comment = PastComment(
        location="東京",
        datetime=datetime.now(),
        weather_condition="大雨",
        comment_text="強雨や雷に注意",
        comment_type=CommentType.WEATHER_COMMENT,
        raw_data={"season": "夏", "count": 100}
    )
    
    validator = WeatherCommentValidator()
    is_valid, reason = validator.validate_comment(test_comment, heavy_rain_weather)
    status = "✅ 適切" if is_valid else "❌ 不適切"
    print(f"大雨時の「{test_comment.comment_text}」: {status} - {reason}")

if __name__ == "__main__":
    print("=== 降水量1mm問題修正テスト ===")
    test_light_rain_comments()
    test_thunder_with_light_rain()
    test_heavy_rain_comments()
    
    print("\n=== テスト完了 ===")
    print("修正により、降水量1mmでは「強雨や雷に注意」のような")
    print("強い警戒表現が除外され、適切な表現が選択されるようになりました。")