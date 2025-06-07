"""
ワークフロー実行サンプルスクリプト

コメント生成ワークフローの動作確認用スクリプト
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# パスの設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.comment_generation_workflow import run_comment_generation

# 環境変数の読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("天気コメント生成ワークフロー - 実行サンプル")
    print("=" * 60)
    
    # パラメータ設定
    location_name = "稚内"
    target_datetime = datetime.now()
    llm_provider = "openai"
    
    print(f"\n実行パラメータ:")
    print(f"  地点名: {location_name}")
    print(f"  対象日時: {target_datetime}")
    print(f"  LLMプロバイダー: {llm_provider}")
    
    print("\nワークフロー実行中...")
    
    # ワークフロー実行
    result = run_comment_generation(
        location_name=location_name,
        target_datetime=target_datetime,
        llm_provider=llm_provider,
        include_debug_info=True  # デバッグ情報を含める
    )
    
    # 結果表示
    print("\n" + "=" * 60)
    print("実行結果")
    print("=" * 60)
    
    if result["success"]:
        print(f"\n✅ 実行成功!")
        print(f"\n生成されたコメント: 「{result['final_comment']}」")
        
        # メタデータ表示
        metadata = result.get("generation_metadata", {})
        print(f"\n📊 実行統計:")
        print(f"  - 総実行時間: {result['execution_time_ms']:.0f}ms")
        print(f"  - リトライ回数: {result['retry_count']}回")
        print(f"  - 地点: {metadata.get('location_name', '不明')}")
        print(f"  - 天気: {metadata.get('weather_condition', '不明')}")
        print(f"  - 気温: {metadata.get('temperature', '不明')}°C")
        
        # ノード実行時間
        if "node_execution_times" in result:
            print(f"\n⏱️  ノード実行時間:")
            for node_name, time_ms in result["node_execution_times"].items():
                print(f"  - {node_name}: {time_ms:.0f}ms")
        
        # 選択されたコメント
        if "selected_past_comments" in metadata:
            print(f"\n📝 参考にした過去コメント:")
            for comment in metadata["selected_past_comments"]:
                print(f"  - {comment['type']}: 「{comment['text']}」")
        
        # 警告
        if result.get("warnings"):
            print(f"\n⚠️  警告:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
    
    else:
        print(f"\n❌ 実行失敗")
        print(f"エラー: {result.get('error', '不明なエラー')}")
    
    print("\n" + "=" * 60)


def test_multiple_locations():
    """複数地点でのテスト実行"""
    print("\n複数地点でのテスト実行")
    print("=" * 60)
    
    locations = ["稚内", "東京", "大阪", "那覇"]
    
    for location in locations:
        print(f"\n{location}の天気コメント生成:")
        result = run_comment_generation(
            location_name=location,
            llm_provider="openai"
        )
        
        if result["success"]:
            print(f"  ✅ {result['final_comment']}")
        else:
            print(f"  ❌ エラー: {result.get('error', '不明')}")


def test_retry_scenario():
    """リトライシナリオのテスト"""
    print("\nリトライシナリオのテスト")
    print("=" * 60)
    
    # 意図的に長いコメントを生成させるような条件を作る
    result = run_comment_generation(
        location_name="東京",
        llm_provider="openai",
        # テスト用のパラメータ
        force_long_comment=True  # このパラメータは実際のノードで処理される必要がある
    )
    
    print(f"\nリトライ回数: {result['retry_count']}")
    print(f"最終コメント: {result.get('final_comment', 'なし')}")


if __name__ == "__main__":
    # 実行モードの選択
    import argparse
    parser = argparse.ArgumentParser(description="ワークフロー実行サンプル")
    parser.add_argument("--mode", choices=["single", "multiple", "retry"], 
                        default="single", help="実行モード")
    args = parser.parse_args()
    
    if args.mode == "single":
        main()
    elif args.mode == "multiple":
        test_multiple_locations()
    elif args.mode == "retry":
        test_retry_scenario()
