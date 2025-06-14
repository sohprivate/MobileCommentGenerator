#!/usr/bin/env python3
"""Test special weather conditions handling"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection
from src.nodes.output_node import _determine_final_comment
from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import PastComment, CommentType
from datetime import datetime

def create_mock_comment(text, comment_type):
    """モックコメントを作成"""
    return PastComment(
        location="テスト地点",
        datetime=datetime.now(),
        weather_condition="test",
        comment_text=text,
        comment_type=comment_type,
        raw_data={"season": "test"}
    )

def test_special_weather_conditions():
    """特殊気象条件のテスト"""
    
    test_cases = [
        {
            "name": "雷雨",
            "weather_condition": WeatherCondition.THUNDER,
            "weather_description": "雷雨",
            "inappropriate_comment": "穏やかな空　過ごしやすい体感",
            "expected_contains": ["雷", "屋内"]
        },
        {
            "name": "霧",
            "weather_condition": WeatherCondition.FOG, 
            "weather_description": "霧",
            "inappropriate_comment": "青空広がる　散歩日和",
            "expected_contains": ["霧", "視界", "運転", "注意"]
        },
        {
            "name": "嵐",
            "weather_condition": WeatherCondition.STORM,
            "weather_description": "嵐",
            "inappropriate_comment": "お出かけ日和　外出がオススメ",
            "expected_contains": ["荒れ", "外出", "控え"]
        },
        {
            "name": "大雨",
            "weather_condition": WeatherCondition.HEAVY_RAIN,
            "weather_description": "大雨",
            "inappropriate_comment": "快適な空　ピクニック日和",
            "expected_contains": ["大雨", "警戒", "冠水", "注意"]
        }
    ]
    
    for case in test_cases:
        print(f"\n🧪 Testing {case['name']} condition:")
        print(f"   Weather: {case['weather_description']}")
        print(f"   Input: '{case['inappropriate_comment']}'")
        
        # Create test weather data
        weather_data = WeatherForecast(
            location="テスト地点",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code=case['weather_condition'].value,
            weather_condition=case['weather_condition'],
            weather_description=case['weather_description'],
            precipitation=10.0,
            humidity=80.0,
            wind_speed=15.0,
            wind_direction=WindDirection.UNKNOWN,
            wind_direction_degrees=0
        )
        
        # Create mock state with inappropriate comment
        state = CommentGenerationState(
            location_name="テスト地点",
            target_datetime=datetime.now(),
            llm_provider="test"
        )
        state.weather_data = weather_data
        
        # Create inappropriate comment pair
        parts = case['inappropriate_comment'].split('　')
        weather_comment = create_mock_comment(parts[0], CommentType.WEATHER_COMMENT)
        advice_comment = create_mock_comment(parts[1], CommentType.ADVICE)
        
        state.selected_pair = CommentPair(
            weather_comment=weather_comment,
            advice_comment=advice_comment,
            similarity_score=1.0,
            selection_reason="test"
        )
        
        # Test the correction
        try:
            result = _determine_final_comment(state)
            print(f"   Output: '{result}'")
            
            # Check if correction was applied
            if any(keyword in result for keyword in case['expected_contains'][:2]):
                print(f"   ✅ PASS: Appropriate correction applied")
            else:
                print(f"   ❌ FAIL: No appropriate correction found")
                print(f"   Expected keywords: {case['expected_contains']}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n{'='*60}")
    print("Test completed!")

if __name__ == "__main__":
    test_special_weather_conditions()