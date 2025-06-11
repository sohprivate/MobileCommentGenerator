"""
ワークフロー統合デモ

エンドツーエンドでワークフローの動作を確認するデモスクリプト
"""

import json
import logging
from datetime import datetime, timedelta
from pprint import pprint

from src.workflows.comment_generation_workflow import run_comment_generation

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def demo_basic_generation():
    """基本的なコメント生成デモ"""
    print("\n" + "=" * 60)
    print("基本的なコメント生成デモ")
    print("=" * 60)

    result = run_comment_generation(location_name="東京", target_datetime=datetime.now())

    print("\n実行結果:")
    print(f"成功: {result['success']}")
    print(f"最終コメント: {result['final_comment']}")
    print(f"実行時間: {result['execution_time_ms']}ms")
    print(f"リトライ回数: {result['retry_count']}")

    if result.get("generation_metadata"):
        print("\nメタデータ:")
        pprint(result["generation_metadata"])

    return result


def demo_with_preferences():
    """ユーザー設定を含むデモ"""
    print("\n" + "=" * 60)
    print("ユーザー設定を含むコメント生成デモ")
    print("=" * 60)

    preferences = {
        "style": "friendly",
        "length": "short",
        "emoji_usage": True,
        "positivity": "positive",
    }

    result = run_comment_generation(
        location_name="稚内",
        target_datetime=datetime.now() + timedelta(days=1),
        user_preferences=preferences,
        include_debug_info=True,
    )

    print("\n実行結果:")
    print(f"成功: {result['success']}")
    print(f"最終コメント: {result['final_comment']}")

    # デバッグ情報が含まれている場合
    if result.get("generation_metadata", {}).get("debug_info"):
        print("\nデバッグ情報:")
        pprint(result["generation_metadata"]["debug_info"])

    return result


def demo_error_handling():
    """エラーハンドリングのデモ"""
    print("\n" + "=" * 60)
    print("エラーハンドリングデモ")
    print("=" * 60)

    # 無効な入力でエラーを発生させる
    result = run_comment_generation(location_name="", llm_provider="invalid_provider")  # 空の地点名

    print("\n実行結果:")
    print(f"成功: {result['success']}")

    if not result["success"]:
        print(f"エラー: {result.get('error', '不明なエラー')}")
    else:
        print(f"最終コメント: {result['final_comment']}")
        if result.get("generation_metadata", {}).get("errors"):
            print("\nエラー情報:")
            for error in result["generation_metadata"]["errors"]:
                print(f"  - {error}")

    return result


def demo_multiple_locations():
    """複数地点でのコメント生成デモ"""
    print("\n" + "=" * 60)
    print("複数地点でのコメント生成デモ")
    print("=" * 60)

    locations = ["稚内", "東京", "大阪", "那覇", "未知の地点"]
    results = []

    for location in locations:
        print(f"\n--- {location} ---")
        result = run_comment_generation(location_name=location, target_datetime=datetime.now())

        if result["success"]:
            print(f"コメント: {result['final_comment']}")
            if result.get("generation_metadata"):
                weather = result["generation_metadata"].get("weather_condition", "不明")
                temp = result["generation_metadata"].get("temperature", "不明")
                print(f"天気: {weather}, 気温: {temp}度")
        else:
            print(f"エラー: {result.get('error', '不明')}")

        results.append(result)

    return results


def demo_retry_scenario():
    """リトライシナリオのデモ"""
    print("\n" + "=" * 60)
    print("リトライシナリオのデモ（モック環境でのテスト）")
    print("=" * 60)

    # 実際のリトライは評価基準に依存するため、
    # ここでは設定値の確認のみ
    result = run_comment_generation(
        location_name="東京",
        target_datetime=datetime.now(),
        # 低品質なコメントを強制的に生成する設定（実際には機能しない）
        user_preferences={"force_low_quality": True, "style": "casual"},  # この設定は無視される
    )

    print("\n実行結果:")
    print(f"成功: {result['success']}")
    print(f"最終コメント: {result['final_comment']}")
    print(f"リトライ回数: {result['retry_count']}")

    return result


def main():
    """メインデモ実行"""
    print("MobileCommentGenerator ワークフロー統合デモ")
    print("=" * 60)

    demos = [
        ("基本的なコメント生成", demo_basic_generation),
        ("ユーザー設定付き", demo_with_preferences),
        ("エラーハンドリング", demo_error_handling),
        ("複数地点", demo_multiple_locations),
        ("リトライシナリオ", demo_retry_scenario),
    ]

    for demo_name, demo_func in demos:
        try:
            print(f"\n\n{'#'*60}")
            print(f"# {demo_name}")
            print("#" * 60)
            demo_func()
        except Exception as e:
            print(f"\nデモ実行中にエラー: {str(e)}")
            import traceback

            traceback.print_exc()

    print("\n\n" + "=" * 60)
    print("デモ完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
