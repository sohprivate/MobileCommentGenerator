#!/usr/bin/env python3
"""Test temperature-based filtering for advice comments"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nodes.select_comment_pair_node import _should_exclude_advice_comment
from src.data.weather_data import WeatherForecast, WeatherCondition
from datetime import datetime

# Create test weather data for rainy conditions at 24°C
from src.data.weather_data import WindDirection

weather_data = WeatherForecast(
    location="佐賀",
    datetime=datetime.now(),
    temperature=24.0,
    weather_code="rain",
    weather_condition=WeatherCondition.RAIN,
    weather_description="雨",
    precipitation=1.0,
    humidity=94.0,
    wind_speed=7.0,
    wind_direction=WindDirection.UNKNOWN,
    wind_direction_degrees=0,
    visibility=10.0,
    uv_index=2
)

# Test comments
test_comments = [
    "熱中症に注意",
    "花粉飛散に注意", 
    "傘を忘れずに",
    "雨に注意して",
    "防寒を万全に",
    "室内で過ごそう"
]

print(f"Testing temperature filtering for {weather_data.temperature}°C rainy weather:")
print("=" * 60)

for comment in test_comments:
    should_exclude = _should_exclude_advice_comment(comment, weather_data)
    status = "❌ EXCLUDED" if should_exclude else "✅ ALLOWED"
    print(f"{status}: '{comment}'")

print("\nExpected results:")
print("❌ EXCLUDED: '熱中症に注意' (too cold for heat stroke warnings)")
print("❌ EXCLUDED: '防寒を万全に' (too warm for cold warnings)")
print("✅ ALLOWED: '傘を忘れずに' (appropriate for rain)")
print("✅ ALLOWED: '雨に注意して' (appropriate for rain)")