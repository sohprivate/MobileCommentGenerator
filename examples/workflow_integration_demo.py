"""
LangGraphワークフロー統合サンプル

Issue #17の実装デモンストレーション
"""

import logging
from datetime import datetime
from src.workflows import run_comment_generation

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demonstrate_basic_workflow():
    """基本的なワークフローの実行デモ"""
    print("\n=== 基本的なワークフロー実行 ===")
    
    result = run_comment_generation(
        location_name="東京",
        target_datetime=datetime.now(),
        llm_provider="openai"
    )
    
    if result["success"]:
        print(f"✅ 生成成功!")
        print(f"  コメント: {result['final_comment']}")
        print(f"  実行時間: {result['generation_metadata'].get('execution_time_ms', 0)}ms")
        print(f"  リトライ回数: {result['generation_metadata'].get('retry_count', 0)}")
    else:
        print(f"❌ 生成失敗: {result['error']}")


def demonstrate_retry_mechanism():
    """リトライメカニズムのデモ（モックノードで自動的にリトライが発生）"""
    print("\n=== リトライメカニズムのデモ ===")
    
    result = run_comment_generation(
        location_name="札幌",
        target_datetime=datetime.now(),
        llm_provider="gemini"
    )
    
    if result["success"]:
        metadata = result["generation_metadata"]
        print(f"✅ 生成成功（リトライあり）")
        print(f"  コメント: {result['final_comment']}")
        print(f"  リトライ回数: {metadata.get('retry_count', 0)}回")
        print(f"  最終的な検証結果: {metadata.get('validation_passed', False)}")


def demonstrate_different_providers():
    """異なるLLMプロバイダーでの実行デモ"""
    print("\n=== 異なるLLMプロバイダー ===")
    
    providers = ["openai", "gemini", "anthropic"]
    locations = ["東京", "大阪", "福岡"]
    
    for provider, location in zip(providers, locations):
        print(f"\n{provider.upper()} - {location}:")
        result = run_comment_generation(
            location_name=location,
            llm_provider=provider
        )
        
        if result["success"]:
            print(f"  ✅ {result['final_comment']}")
        else:
            print(f"  ❌ エラー: {result['error']}")


def demonstrate_error_handling():
    """エラーハンドリングのデモ"""
    print("\n=== エラーハンドリング ===")
    
    # 地点名が空の場合
    print("\n1. 地点名が空:")
    result = run_comment_generation(
        location_name="",
        llm_provider="openai"
    )
    print(f"  結果: {'成功' if result['success'] else 'エラー'}")
    if not result["success"]:
        print(f"  エラー詳細: {result['error']}")
    
    # 無効なLLMプロバイダー（実際のノードでは処理される）
    print("\n2. 無効なLLMプロバイダー:")
    result = run_comment_generation(
        location_name="東京",
        llm_provider="invalid_provider"
    )
    print(f"  結果: {'成功' if result['success'] else 'エラー'}")
    if result["success"]:
        print(f"  コメント: {result['final_comment']}")


def display_workflow_status():
    """ワークフローの実装状況表示"""
    print("\n=== LangGraphワークフロー実装状況 ===")
    print("✅ 実装済み:")
    print("  - ワークフロー骨格 (comment_generation_workflow.py)")
    print("  - モックノード (mock_nodes.py)")
    print("  - 表現ルール設定 (expression_rules.yaml)")
    print("  - テストスイート (test_comment_generation_workflow.py)")
    print("\n🔄 統合済みの実装ノード:")
    print("  - FetchForecastNode (天気予報取得)")
    print("  - RetrievePastCommentsNode (過去コメント取得)")
    print("  - GenerateCommentNode (LLMコメント生成)")
    print("\n🚧 実装待ちノード（モック使用中）:")
    print("  - InputNode")
    print("  - SelectCommentPairNode")
    print("  - EvaluateCandidateNode")
    print("  - OutputNode")


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("LangGraphワークフロー統合デモ")
    print("Issue #17: LangGraphワークフロー実装の加速")
    print("=" * 60)
    
    # ワークフロー実装状況
    display_workflow_status()
    
    # 各種デモンストレーション
    demonstrate_basic_workflow()
    demonstrate_retry_mechanism()
    demonstrate_different_providers()
    demonstrate_error_handling()
    
    print("\n" + "=" * 60)
    print("デモ完了!")
    print("次のステップ: Issue #5, #6 の実装とワークフローへの統合")
    print("=" * 60)


if __name__ == "__main__":
    main()
