#!/usr/bin/env python3
"""
接続テストスクリプト

S3、LLM、気象APIへの接続を確認します。
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数を読み込み
load_dotenv()


def test_weather_api():
    """気象API接続テスト"""
    print("\n" + "="*60)
    print("【気象API接続テスト】")
    print("="*60)
    
    try:
        from src.apis.wxtech_client import WxTechAPIClient
        
        api_key = os.getenv("WXTECH_API_KEY")
        if not api_key:
            print("❌ エラー: WXTECH_API_KEY環境変数が設定されていません")
            return False
        
        print(f"✓ APIキーが見つかりました: {api_key[:10]}...")
        
        # 東京の天気を取得
        client = WxTechAPIClient(api_key)
        lat, lon = 35.6762, 139.6503  # 東京
        
        print(f"テスト地点: 東京 (緯度: {lat}, 経度: {lon})")
        
        try:
            forecast_collection = client.get_forecast(lat, lon)
            
            if forecast_collection and forecast_collection.forecasts:
                current = forecast_collection.get_nearest_forecast(datetime.now())
                if current:
                    print(f"✅ 気象API接続成功!")
                    print(f"  - 天気: {current.weather_description}")
                    print(f"  - 気温: {current.temperature}°C")
                    print(f"  - 湿度: {current.humidity}%")
                    print(f"  - 風速: {current.wind_speed}m/s")
                    return True
                else:
                    print("❌ 現在時刻の予報データが取得できませんでした")
                    return False
            else:
                print("❌ 予報データが空です")
                return False
                
        except Exception as e:
            print(f"❌ API呼び出しエラー: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False


def test_s3_connection():
    """S3接続テスト"""
    print("\n" + "="*60)
    print("【S3接続テスト】")
    print("="*60)
    
    try:
        from src.repositories.s3_comment_repository import S3CommentRepository
        
        # AWSプロファイルを使用
        aws_profile = os.getenv("AWS_PROFILE", "dit-training")
        region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
        bucket_name = os.getenv("S3_COMMENT_BUCKET", "it-literacy-457604437098-ap-northeast-1")
        
        print(f"✓ AWSプロファイル '{aws_profile}' を使用します")
        print(f"  - リージョン: {region}")
        print(f"  - バケット: {bucket_name}")
        
        # リポジトリを初期化（プロファイルを指定）
        repo = S3CommentRepository(
            bucket_name=bucket_name,
            region_name=region,
            aws_profile=aws_profile
        )
        
        # 最新のコメントを取得してテスト
        print("最新の過去コメントを取得中...")
        
        try:
            # get_recent_commentsメソッドを使用
            comment_collection = repo.get_recent_comments(location="東京", max_comments=5)
            past_comments = comment_collection.comments if comment_collection else []
            
            if past_comments:
                print(f"✅ S3接続成功! {len(past_comments)}件のコメントを取得")
                
                # 最初のコメントを表示
                if past_comments:
                    first_comment = past_comments[0]
                    print(f"  サンプルコメント:")
                    print(f"  - テキスト: {first_comment.comment_text}")
                    print(f"  - 地点: {first_comment.location}")
                    print(f"  - 天気: {first_comment.weather_condition}")
                    print(f"  - タイプ: {first_comment.comment_type.value}")
                return True
            else:
                print("❌ コメントが見つかりませんでした")
                return False
                
        except Exception as e:
            print(f"❌ S3アクセスエラー: {str(e)}")
            return False
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False


def test_llm_connection():
    """LLM接続テスト"""
    print("\n" + "="*60)
    print("【LLM接続テスト】")
    print("="*60)
    
    try:
        from src.llm.llm_manager import LLMManager
        
        # 各プロバイダーをテスト
        providers = ["openai", "anthropic", "gemini"]
        
        for provider in providers:
            print(f"\n--- {provider.upper()} テスト ---")
            
            # 環境変数チェック
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                env_var = "OPENAI_API_KEY"
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                env_var = "ANTHROPIC_API_KEY"
            elif provider == "gemini":
                api_key = os.getenv("GOOGLE_API_KEY")
                env_var = "GOOGLE_API_KEY"
            
            if not api_key:
                print(f"⚠️  {env_var}が設定されていません（スキップ）")
                continue
            
            print(f"✓ APIキーが見つかりました: {api_key[:10]}...")
            
            try:
                # LLMマネージャーを初期化
                llm_manager = LLMManager(provider=provider)
                
                # 簡単なテストプロンプト
                test_prompt = "こんにちは。これは接続テストです。「接続成功」と返答してください。"
                
                print(f"テストプロンプトを送信中...")
                response = llm_manager.generate(test_prompt)
                
                if response and "接続成功" in response:
                    print(f"✅ {provider.upper()}接続成功!")
                    print(f"  レスポンス: {response[:100]}...")
                else:
                    print(f"❌ 期待されたレスポンスが返されませんでした")
                    print(f"  レスポンス: {response[:100] if response else 'None'}")
                    
            except Exception as e:
                print(f"❌ {provider.upper()}接続エラー: {str(e)}")
        
        return True  # 少なくとも1つのプロバイダーが設定されていればOK
        
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False


def test_integration():
    """統合テスト（ワークフロー実行）"""
    print("\n" + "="*60)
    print("【統合テスト】")
    print("="*60)
    
    try:
        from src.workflows.comment_generation_workflow import run_comment_generation
        
        print("コメント生成ワークフローを実行中...")
        print("  地点: 東京")
        print("  LLMプロバイダー: openai")
        
        result = run_comment_generation(
            location_name="東京",
            llm_provider="openai"
        )
        
        if result.get("success"):
            print("✅ ワークフロー実行成功!")
            print(f"  最終コメント: {result.get('final_comment')}")
            print(f"  実行時間: {result.get('execution_time_ms')}ms")
            
            # メタデータの表示
            metadata = result.get("generation_metadata", {})
            if metadata:
                selection_metadata = metadata.get("selection_metadata", {})
                if selection_metadata:
                    print(f"  選択方法: {selection_metadata.get('selection_method', 'unknown')}")
                    print(f"  天気コメント候補数: {selection_metadata.get('weather_comments_count', 0)}")
                    print(f"  アドバイス候補数: {selection_metadata.get('advice_comments_count', 0)}")
            
            return True
        else:
            print("❌ ワークフロー実行失敗")
            print(f"  エラー: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 統合テストエラー: {str(e)}")
        return False


def main():
    """メインテスト実行"""
    print("\n" + "="*80)
    print("API接続テストを開始します")
    print("="*80)
    
    # AWS_PROFILEが設定されていない場合はdit-trainingを使用
    if not os.getenv("AWS_PROFILE"):
        os.environ["AWS_PROFILE"] = "dit-training"
        print(f"AWS_PROFILE環境変数を 'dit-training' に設定しました")
    
    # 各テストを実行
    results = {
        "気象API": test_weather_api(),
        "S3": test_s3_connection(),
        "LLM": test_llm_connection(),
        "統合": test_integration()
    }
    
    # 結果サマリー
    print("\n" + "="*80)
    print("【テスト結果サマリー】")
    print("="*80)
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    # 全体の成功/失敗
    all_success = all(results.values())
    
    print("\n" + "="*80)
    if all_success:
        print("✅ すべてのテストが成功しました！")
    else:
        print("❌ 一部のテストが失敗しました。上記のエラーメッセージを確認してください。")
    print("="*80)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())