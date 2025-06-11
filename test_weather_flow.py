#!/usr/bin/env python
"""気象データフローの完全テスト"""

import os
os.environ["AWS_PROFILE"] = "dit-training"

from src.workflows.comment_generation_workflow import run_comment_generation
import json

def test_weather_flow():
    """気象データが正しく使用されているか確認"""
    
    locations = ["東京", "大阪", "札幌"]
    
    for location in locations:
        print(f"\n{'='*60}")
        print(f"Testing: {location}")
        print("="*60)
        
        try:
            result = run_comment_generation(
                location_name=location,
                llm_provider="openai"
            )
            
            if result.get("success"):
                print(f"✅ Success!")
                print(f"Final comment: {result.get('final_comment')}")
                
                # メタデータから気象情報を表示
                metadata = result.get('generation_metadata', {})
                print(f"\nWeather data used:")
                print(f"  Temperature: {metadata.get('temperature')}°C")
                print(f"  Weather: {metadata.get('weather_condition')}")
                print(f"  Location coords: {metadata.get('location_coordinates')}")
                
                # 選択されたS3コメントを表示
                selected_comments = metadata.get('selected_past_comments', [])
                print(f"\nSelected S3 comments:")
                for comment in selected_comments:
                    if comment:
                        print(f"  - {comment.get('type')}: {comment.get('text')}")
                        
            else:
                print(f"❌ Failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_weather_flow()