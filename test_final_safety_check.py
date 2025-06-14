#!/usr/bin/env python3
"""Test the final safety check logic"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.comment_config import get_comment_config

# Test the safety check logic
config = get_comment_config()
weather_description = "大雨・嵐"
temperature = 24.0

current_weather = weather_description.lower()
is_rain = any(rain_word in current_weather for rain_word in ["雨", "大雨", "豪雨", "嵐"])
is_low_temp = temperature < config.heat_warning_threshold

print(f"Testing safety check for:")
print(f"Weather: {weather_description}")
print(f"Temperature: {temperature}°C")
print(f"Heat threshold: {config.heat_warning_threshold}°C")
print(f"Is rain: {is_rain}")
print(f"Is low temp: {is_low_temp}")

# Test advice comment
advice_comment = "熱中症に注意"
should_replace_advice = is_rain and is_low_temp and advice_comment and "熱中症" in advice_comment

print(f"\nAdvice comment: '{advice_comment}'")
print(f"Should replace advice: {should_replace_advice}")

# Test weather comment  
weather_comment = "ムシムシ暑い"
should_replace_weather = any(severe in current_weather for severe in ["大雨", "嵐", "豪雨"]) and weather_comment
if should_replace_weather:
    should_replace_weather = any(comfort in weather_comment for comfort in ["穏やか", "快適", "過ごしやすい", "ムシムシ"])

print(f"\nWeather comment: '{weather_comment}'")
print(f"Should replace weather: {should_replace_weather}")

if should_replace_advice or should_replace_weather:
    print("\n✅ Safety check would trigger!")
else:
    print("\n❌ Safety check would NOT trigger!")