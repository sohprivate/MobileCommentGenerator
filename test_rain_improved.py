#!/usr/bin/env python
"""改善された雨天時のコメント選択テスト"""

import os
os.environ["AWS_PROFILE"] = "dit-training"

from datetime import datetime
from src.data.comment_generation_state import CommentGenerationState
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.nodes.select_comment_pair_node import select_comment_pair_node
from src.nodes.retrieve_past_comments_node import retrieve_past_comments_node

# テスト用の雨天データを作成
weather_data = WeatherForecast(
    location="東京",
    datetime=datetime.now(),
    weather_condition=WeatherCondition.RAIN,
    weather_description="雨",
    temperature=24.0,
    humidity=95,
    wind_speed=6,
    precipitation=9.0,
    weather_code="rain",
    wind_direction=None,
    wind_direction_degrees=0,
    raw_data={}
)

# 状態を初期化
state = CommentGenerationState(
    location_name="東京",
    target_datetime=datetime.now()
)
state.weather_data = weather_data
state.llm_provider = "openai"

print("改善された雨天時のコメント選択をテスト中...")
print(f"天気条件: {weather_data.weather_description}")
print(f"気温: {weather_data.temperature}°C")
print(f"降水量: {weather_data.precipitation}mm")

# 過去コメントを取得
state = retrieve_past_comments_node(state)
print(f"\n取得したコメント数: {len(state.past_comments) if state.past_comments else 0}")

# コメントペアを選択
state = select_comment_pair_node(state)

if state.selected_pair:
    print(f"\n✅ 選択成功!")
    print(f"天気コメント: {state.selected_pair.weather_comment.comment_text}")
    print(f"アドバイス: {state.selected_pair.advice_comment.comment_text}")
    
    # 禁止表現チェック
    forbidden_phrases = ["過ごしやすい", "快適", "体感", "心地", "爽やか"]
    for phrase in forbidden_phrases:
        if phrase in state.selected_pair.weather_comment.comment_text:
            print(f"\n⚠️ 警告: 天気コメントに禁止表現 '{phrase}' が含まれています!")
        if phrase in state.selected_pair.advice_comment.comment_text:
            print(f"\n⚠️ 警告: アドバイスに禁止表現 '{phrase}' が含まれています!")
else:
    print(f"\n❌ 選択失敗")
    if state.errors:
        for error in state.errors:
            print(f"  - {error}")