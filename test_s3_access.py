#!/usr/bin/env python3
"""S3アクセステストスクリプト - DEPRECATED

注意: このスクリプトは古い実装に関するものです。
現在、システムはS3の代わりにローカルCSVファイルを使用するように変更されました。
"""

import os
import sys
import boto3
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.repositories.s3_comment_repository import S3CommentRepository

def test_s3_access(use_profile=True):
    """S3アクセスをテスト
    
    Args:
        use_profile: Trueの場合、dit-trainingプロファイルを使用
    """
    print("=== S3アクセステスト ===\n")
    
    bucket_name = 'it-literacy-457604437098-ap-northeast-1'
    region_name = 'ap-northeast-1'
    
    if use_profile:
        print("🔑 AWS Profile: dit-training を使用\n")
        
        # プロファイルを使用してセッションを作成
        session = boto3.Session(profile_name='dit-training')
        
        # 認証情報の確認
        try:
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            print("1. AWS認証情報:")
            print(f"  Account: {identity['Account']}")
            print(f"  Role: {identity['Arn'].split('/')[-2]}")
            print(f"  User: {identity['Arn'].split('/')[-1]}")
        except Exception as e:
            print(f"  ❌ 認証情報の取得失敗: {str(e)}")
            return
    else:
        print("🔑 環境変数のAWS認証情報を使用\n")
        
        # 環境変数の確認
        print("1. 環境変数の確認:")
        env_vars = {
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', region_name),
            'S3_COMMENT_BUCKET': os.getenv('S3_COMMENT_BUCKET', bucket_name)
        }
        
        for key, value in env_vars.items():
            if key == 'AWS_SECRET_ACCESS_KEY' and value:
                print(f"  {key}: {'*' * 8}...{value[-4:]}")
            elif value:
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: ❌ 未設定")
    
    print("\n2. S3接続テスト:")
    
    try:
        # S3クライアントの作成
        if use_profile:
            s3_client = session.client('s3', region_name=region_name)
        else:
            s3_client = boto3.client('s3', region_name=region_name)
        
        # リポジトリの作成（プロファイル使用時は直接クライアントを渡す）
        repo = S3CommentRepository(
            bucket_name=bucket_name,
            region_name=region_name
        )
        repo.s3_client = s3_client  # クライアントを差し替え
        
        # 接続テスト
        if repo.test_connection():
            print("  ✅ S3バケットへの接続成功!")
            
            # 利用可能期間の確認
            print("\n3. 利用可能なデータ期間:")
            periods = repo.list_available_periods()
            if periods:
                print(f"  利用可能期間: {len(periods)}件")
                print(f"  最新: {periods[0]}")
                print(f"  最古: {periods[-1]}")
                
                # 最新データのサンプル取得
                print("\n4. 最新データのサンプル取得:")
                latest_period = periods[0]
                collection = repo.fetch_comments_by_period(latest_period)
                print(f"  期間 {latest_period} のコメント数: {len(collection.comments)}件")
                
                if collection.comments:
                    sample = collection.comments[0]
                    print(f"\n  📝 サンプルコメント:")
                    print(f"    日時: {sample.datetime}")
                    print(f"    地点: {sample.location}")
                    print(f"    天気: {sample.weather_condition}")
                    print(f"    コメント: {sample.comment_text[:50]}...")
            else:
                print("  ⚠️  利用可能なデータがありません")
                
        else:
            print("  ❌ S3バケットへの接続失敗")
            print("\n考えられる原因:")
            print("  - AWS認証情報が正しくない")
            print("  - S3バケットへのアクセス権限がない")
            print("  - ネットワーク接続の問題")
            
    except Exception as e:
        print(f"  ❌ エラー発生: {str(e)}")
        print("\n対処方法:")
        if use_profile:
            print("  1. dit-trainingプロファイルが正しく設定されているか確認:")
            print("     aws configure list --profile dit-training")
            print("  2. プロファイルでのアクセス確認:")
            print("     aws s3 ls s3://it-literacy-457604437098-ap-northeast-1 --profile dit-training")
        else:
            print("  1. .envファイルにAWS認証情報が正しく設定されているか確認")
            print("  2. 環境変数のトークンが期限切れの可能性があります")
            print("  3. IAMユーザーに必要な権限があるか確認:")
            print("     - s3:GetObject")
            print("     - s3:ListBucket") 
            print("     - s3:HeadBucket")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='S3アクセステスト')
    parser.add_argument(
        '--no-profile', 
        action='store_true',
        help='環境変数のAWS認証情報を使用（デフォルト: dit-trainingプロファイルを使用）'
    )
    
    args = parser.parse_args()
    test_s3_access(use_profile=not args.no_profile)