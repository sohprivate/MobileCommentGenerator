#!/usr/bin/env python3
"""天気コメント検証システムのテストスクリプト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.data.past_comment import PastComment, CommentType


def create_test_weather_data(description: str, temperature: float, humidity: float = 60) -> WeatherForecast:
    """テスト用の天気データを作成"""
    return WeatherForecast(
        location="テスト地点",
        datetime=datetime.now(),
        temperature=temperature,
        weather_code="01",
        weather_condition=WeatherCondition.RAIN,  # 適当な値
        weather_description=description,
        precipitation=0.0,
        humidity=humidity,
        wind_speed=3.0,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0,
        uv_index=3,
        visibility=10.0
    )


def create_test_comment(text: str, comment_type: CommentType) -> PastComment:
    """テスト用のコメントを作成"""
    return PastComment(
        location="テスト地点",
        datetime=datetime.now(),
        weather_condition="テスト",
        comment_text=text,
        comment_type=comment_type,
        raw_data={"count": 100, "season": "夏"}
    )


def test_rainy_weather_filtering():
    """雨天時のフィルタリングテスト"""
    print("🌧️ 雨天時のフィルタリングテスト")
    
    validator = WeatherCommentValidator()
    rainy_weather = create_test_weather_data("雨", 20.0)
    
    # 不適切なコメント（雨天時に除外されるべき）
    inappropriate_comments = [
        create_test_comment("青空が広がって", CommentType.WEATHER_COMMENT),
        create_test_comment("穏やかな空", CommentType.WEATHER_COMMENT),
        create_test_comment("過ごしやすい体感", CommentType.WEATHER_COMMENT),
        create_test_comment("お出かけ日和", CommentType.ADVICE),
        create_test_comment("散歩におすすめ", CommentType.ADVICE),
    ]
    
    # 適切なコメント（雨天時に選ばれるべき）
    appropriate_comments = [
        create_test_comment("雨に注意", CommentType.WEATHER_COMMENT),
        create_test_comment("本格的な雨が降る", CommentType.WEATHER_COMMENT),
        create_test_comment("傘を忘れずに", CommentType.ADVICE),
        create_test_comment("雨具の準備を", CommentType.ADVICE),
    ]
    
    all_comments = inappropriate_comments + appropriate_comments
    
    # フィルタリング実行
    filtered = validator.filter_comments(all_comments, rainy_weather)
    
    print(f"  入力: {len(all_comments)}件")
    print(f"  フィルタリング後: {len(filtered)}件")
    
    # 結果検証
    filtered_texts = [c.comment_text for c in filtered]
    for comment in appropriate_comments:
        if comment.comment_text not in filtered_texts:
            print(f"  ❌ 適切なコメントが除外された: {comment.comment_text}")
        else:
            print(f"  ✅ 適切なコメントが残った: {comment.comment_text}")
    
    for comment in inappropriate_comments:
        if comment.comment_text in filtered_texts:
            print(f"  ❌ 不適切なコメントが残った: {comment.comment_text}")
        else:
            print(f"  ✅ 不適切なコメントが除外された: {comment.comment_text}")


def test_heavy_rain_filtering():
    """大雨時のフィルタリングテスト"""
    print("\n⛈️ 大雨時のフィルタリングテスト")
    
    validator = WeatherCommentValidator()
    heavy_rain_weather = create_test_weather_data("大雨", 18.0)
    
    # 軽微な表現（大雨時は除外されるべき）
    mild_comments = [
        create_test_comment("にわか雨が心配", CommentType.WEATHER_COMMENT),
        create_test_comment("スッキリしない空", CommentType.WEATHER_COMMENT),
        create_test_comment("変わりやすい空", CommentType.WEATHER_COMMENT),
        create_test_comment("蒸し暑い", CommentType.WEATHER_COMMENT),
    ]
    
    # 強い警戒表現（大雨時に選ばれるべき）
    strong_comments = [
        create_test_comment("激しい雨に警戒", CommentType.WEATHER_COMMENT),
        create_test_comment("本格的な雨に注意", CommentType.WEATHER_COMMENT),
        create_test_comment("大雨に備えて", CommentType.ADVICE),
        create_test_comment("安全第一で", CommentType.ADVICE),
    ]
    
    all_comments = mild_comments + strong_comments
    filtered = validator.filter_comments(all_comments, heavy_rain_weather)
    
    print(f"  入力: {len(all_comments)}件")
    print(f"  フィルタリング後: {len(filtered)}件")
    
    # 軽微な表現は除外されるべき
    filtered_texts = [c.comment_text for c in filtered]
    for comment in mild_comments:
        if comment.comment_text in filtered_texts:
            print(f"  ❌ 軽微な表現が残った: {comment.comment_text}")
        else:
            print(f"  ✅ 軽微な表現が除外された: {comment.comment_text}")
    
    # 強い表現は残るべき
    for comment in strong_comments:
        if comment.comment_text not in filtered_texts:
            print(f"  ❌ 強い表現が除外された: {comment.comment_text}")
        else:
            print(f"  ✅ 強い表現が残った: {comment.comment_text}")


def test_temperature_filtering():
    """気温による除外テスト"""
    print("\n🌡️ 気温による除外テスト")
    
    validator = WeatherCommentValidator()
    
    # 低温時（5°C）
    cold_weather = create_test_weather_data("晴れ", 5.0)
    hot_comment = create_test_comment("熱中症に注意", CommentType.ADVICE)
    
    is_valid, reason = validator.validate_comment(hot_comment, cold_weather)
    print(f"  5°Cで熱中症コメント: {'✅ 除外' if not is_valid else '❌ 通過'} ({reason})")
    
    # 高温時（35°C）
    hot_weather = create_test_weather_data("晴れ", 35.0)
    cold_comment = create_test_comment("防寒対策を", CommentType.ADVICE)
    
    is_valid, reason = validator.validate_comment(cold_comment, hot_weather)
    print(f"  35°Cで防寒コメント: {'✅ 除外' if not is_valid else '❌ 通過'} ({reason})")


def test_appropriateness_scoring():
    """適切性スコアリングテスト"""
    print("\n📊 適切性スコアリングテスト")
    
    validator = WeatherCommentValidator()
    heavy_rain_weather = create_test_weather_data("大雨", 20.0)
    
    comments = [
        create_test_comment("激しい雨に警戒", CommentType.WEATHER_COMMENT),
        create_test_comment("にわか雨が心配", CommentType.WEATHER_COMMENT),
        create_test_comment("本格的な雨に注意", CommentType.WEATHER_COMMENT),
        create_test_comment("スッキリしない空", CommentType.WEATHER_COMMENT),
    ]
    
    # スコア計算と表示
    for comment in comments:
        score = validator._calculate_appropriateness_score(comment, heavy_rain_weather)
        print(f"  '{comment.comment_text}': {score:.1f}点")


def main():
    """メインテスト実行"""
    print("🧪 天気コメント検証システムテスト開始\n")
    
    try:
        test_rainy_weather_filtering()
        test_heavy_rain_filtering()
        test_temperature_filtering()
        test_appropriateness_scoring()
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()