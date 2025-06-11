#!/usr/bin/env python
"""雨天時のコメント選択テスト"""

import os
os.environ["AWS_PROFILE"] = "dit-training"

from src.workflows.comment_generation_workflow import run_comment_generation

# 東京の雨天データでテスト
print("雨天時のコメント選択をテスト中...")

try:
    result = run_comment_generation(
        location_name="東京",
        llm_provider="openai"
    )
    
    if result.get("success"):
        print(f"\n✅ 成功!")
        print(f"最終コメント: {result.get('final_comment')}")
        
        metadata = result.get('generation_metadata', {})
        print(f"\n使用された気象データ:")
        print(f"  天気: {metadata.get('weather_condition')}")
        print(f"  気温: {metadata.get('temperature')}°C")
        
        selected = metadata.get('selected_past_comments', [])
        print(f"\n選択されたS3コメント:")
        for comment in selected:
            if comment:
                print(f"  - {comment.get('type')}: {comment.get('text')}")
    else:
        print(f"❌ 失敗: {result.get('error')}")
        
except Exception as e:
    print(f"❌ エラー: {str(e)}")