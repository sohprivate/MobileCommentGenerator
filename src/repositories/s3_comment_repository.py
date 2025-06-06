"""
S3過去コメントリポジトリ

S3バケットから過去コメントJSONLファイルを取得・解析する
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import warnings
from io import StringIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from src.data.past_comment import PastComment, PastCommentCollection, CommentType


# ログ設定
logger = logging.getLogger(__name__)


class S3CommentRepositoryError(Exception):
    """S3コメントリポジトリ関連のエラー"""
    pass


class S3CommentRepository:
    """S3から過去コメントデータを取得するリポジトリクラス
    
    S3バケット: it-literacy-457604437098-ap-northeast-1
    パス構造: downloaded_jsonl_files_archive/YYYYMM/YYYYMM.jsonl
    """
    
    def __init__(
        self,
        bucket_name: str = "it-literacy-457604437098-ap-northeast-1",
        region_name: str = "ap-northeast-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """S3コメントリポジトリを初期化
        
        Args:
            bucket_name: S3バケット名
            region_name: AWSリージョン
            aws_access_key_id: AWSアクセスキーID（Noneの場合は環境変数から取得）
            aws_secret_access_key: AWSシークレットアクセスキー
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # S3クライアントの初期化
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.s3_client = boto3.client(
                    's3',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                # 環境変数またはIAMロールから認証情報を取得
                self.s3_client = boto3.client('s3', region_name=region_name)
                
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise S3CommentRepositoryError(f"AWS認証情報が設定されていません: {str(e)}")
        except Exception as e:
            raise S3CommentRepositoryError(f"S3クライアントの初期化に失敗: {str(e)}")
    
    def test_connection(self) -> bool:
        """S3接続をテスト
        
        Returns:
            接続成功の場合True
        """
        try:
            # バケットの存在確認
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3バケット '{self.bucket_name}' への接続成功")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3バケット '{self.bucket_name}' が見つかりません")
            elif error_code == '403':
                logger.error(f"S3バケット '{self.bucket_name}' へのアクセス権限がありません")
            else:
                logger.error(f"S3接続エラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"S3接続テストでエラー: {str(e)}")
            return False
    
    def list_available_periods(self) -> List[str]:
        """利用可能な期間（YYYYMM）のリストを取得
        
        Returns:
            利用可能な期間のリスト（YYYYMM形式）
        """
        try:
            # downloaded_jsonl_files_archive/ 配下のフォルダ一覧を取得
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="downloaded_jsonl_files_archive/",
                Delimiter="/"
            )
            
            periods = []
            for prefix in response.get('CommonPrefixes', []):
                # downloaded_jsonl_files_archive/YYYYMM/ から YYYYMM を抽出
                folder_path = prefix['Prefix']
                match = re.search(r'downloaded_jsonl_files_archive/(\d{6})/', folder_path)
                if match:
                    periods.append(match.group(1))
            
            periods.sort(reverse=True)  # 新しい順でソート
            logger.info(f"利用可能な期間: {len(periods)}件 ({periods[:5]}...)" if len(periods) > 5 else f"利用可能な期間: {periods}")
            return periods
            
        except ClientError as e:
            logger.error(f"期間リスト取得エラー: {str(e)}")
            raise S3CommentRepositoryError(f"期間リストの取得に失敗: {str(e)}")
    
    def fetch_comments_by_period(
        self,
        period: str,
        location: Optional[str] = None,
        weather_condition: Optional[str] = None
    ) -> PastCommentCollection:
        """指定期間の過去コメントを取得
        
        Args:
            period: 期間（YYYYMM形式）
            location: 地点名でのフィルタリング（オプション）
            weather_condition: 天気状況でのフィルタリング（オプション）
            
        Returns:
            過去コメントコレクション
            
        Raises:
            S3CommentRepositoryError: データ取得に失敗した場合
        """
        # 期間フォーマットの検証
        if not re.match(r'^\d{6}$', period):
            raise ValueError(f"期間は YYYYMM 形式で指定してください: {period}")
        
        # ファイルパスの構築
        file_key = f"downloaded_jsonl_files_archive/{period}/{period}.jsonl"
        
        try:
            # S3からファイルを取得
            logger.info(f"S3ファイル取得開始: {file_key}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            
            # JSONLファイルの内容を読み取り
            content = response['Body'].read().decode('utf-8')
            
            # JSONLデータの解析
            comments = self._parse_jsonl_content(content, file_key)
            
            # コレクション作成
            collection = PastCommentCollection(
                comments=comments,
                source_period=period
            )
            
            # フィルタリング適用
            if location:
                collection = collection.filter_by_location(location)
            
            if weather_condition:
                collection = collection.filter_by_weather_condition(weather_condition)
            
            logger.info(f"コメント取得完了: {len(collection.comments)}件 (期間: {period})")
            return collection
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.warning(f"ファイルが見つかりません: {file_key}")
                return PastCommentCollection(comments=[], source_period=period)
            else:
                logger.error(f"S3ファイル取得エラー: {str(e)}")
                raise S3CommentRepositoryError(f"ファイル取得に失敗: {str(e)}")
    
    def fetch_comments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        location: Optional[str] = None,
        weather_condition: Optional[str] = None,
        max_periods: int = 12
    ) -> PastCommentCollection:
        """日付範囲指定で過去コメントを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            location: 地点名でのフィルタリング
            weather_condition: 天気状況でのフィルタリング
            max_periods: 最大取得期間数（パフォーマンス制限）
            
        Returns:
            過去コメントコレクション
        """
        if start_date > end_date:
            raise ValueError("開始日は終了日より前である必要があります")
        
        # 対象期間のリストを生成
        periods = []
        current_date = start_date.replace(day=1)  # 月初に調整
        
        while current_date <= end_date and len(periods) < max_periods:
            period = current_date.strftime('%Y%m')
            periods.append(period)
            
            # 次の月へ
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        logger.info(f"日付範囲での取得: {start_date.date()} - {end_date.date()} ({len(periods)}期間)")
        
        # 複数期間のコメントを結合
        all_comments = []
        
        for period in periods:
            try:
                period_collection = self.fetch_comments_by_period(
                    period, location, weather_condition
                )
                
                # 日付範囲内のコメントのみを追加
                for comment in period_collection.comments:
                    if start_date <= comment.datetime <= end_date:
                        all_comments.append(comment)
                        
            except S3CommentRepositoryError as e:
                logger.warning(f"期間 {period} のデータ取得に失敗: {str(e)}")
                continue
        
        return PastCommentCollection(
            comments=all_comments,
            source_period=f"{periods[0]}-{periods[-1]}" if periods else None
        )
    
    def get_recent_comments(
        self,
        months_back: int = 3,
        location: Optional[str] = None,
        weather_condition: Optional[str] = None,
        max_comments: int = 100
    ) -> PastCommentCollection:
        """最近の過去コメントを取得
        
        Args:
            months_back: 何ヶ月前まで取得するか
            location: 地点名でのフィルタリング
            weather_condition: 天気状況でのフィルタリング
            max_comments: 最大コメント数
            
        Returns:
            過去コメントコレクション
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        collection = self.fetch_comments_by_date_range(
            start_date, end_date, location, weather_condition, max_periods=months_back
        )
        
        # コメント数制限
        if len(collection.comments) > max_comments:
            # 日付が新しい順にソートして上位を取得
            collection.comments.sort(key=lambda c: c.datetime, reverse=True)
            collection.comments = collection.comments[:max_comments]
            logger.info(f"コメント数を {max_comments} 件に制限")
        
        return collection
    
    def search_similar_comments(
        self,
        target_weather_condition: str,
        target_temperature: Optional[float] = None,
        target_location: Optional[str] = None,
        months_back: int = 6,
        max_results: int = 20,
        min_similarity: float = 0.3
    ) -> List[PastComment]:
        """類似コメントを検索
        
        Args:
            target_weather_condition: 対象の天気状況
            target_temperature: 対象の気温
            target_location: 対象の地点
            months_back: 検索対象期間（月数）
            max_results: 最大結果数
            min_similarity: 最小類似度
            
        Returns:
            類似度順にソートされたコメントリスト
        """
        # 最近のコメントを取得
        collection = self.get_recent_comments(
            months_back=months_back,
            max_comments=1000  # 検索対象を多めに取得
        )
        
        # 類似度計算で絞り込み
        similar_comments = collection.get_similar_comments(
            target_weather_condition=target_weather_condition,
            target_temperature=target_temperature,
            target_location=target_location,
            min_similarity=min_similarity,
            max_results=max_results
        )
        
        logger.info(f"類似コメント検索: {len(similar_comments)}件見つかりました")
        return similar_comments
    
    def _parse_jsonl_content(self, content: str, source_file: str) -> List[PastComment]:
        """JSONLファイルの内容を解析
        
        Args:
            content: JSONLファイルの内容
            source_file: ソースファイル名
            
        Returns:
            過去コメントのリスト
        """
        comments = []
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                comment = PastComment.from_dict(data, source_file)
                comments.append(comment)
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSONデコードエラー {source_file}:{line_num}: {str(e)}")
                continue
            except ValueError as e:
                logger.warning(f"データ検証エラー {source_file}:{line_num}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"コメント解析エラー {source_file}:{line_num}: {str(e)}")
                continue
        
        logger.info(f"JSONLファイル解析完了: {len(comments)}件 (総行数: {len(lines)})")
        return comments
    
    def get_repository_statistics(self) -> Dict[str, Any]:
        """リポジトリの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        try:
            available_periods = self.list_available_periods()
            
            # 最新期間のサンプルデータを取得
            sample_stats = {}
            if available_periods:
                latest_period = available_periods[0]
                try:
                    sample_collection = self.fetch_comments_by_period(latest_period)
                    sample_stats = sample_collection.get_statistics()
                except Exception as e:
                    logger.warning(f"サンプル統計取得エラー: {str(e)}")
            
            return {
                'bucket_name': self.bucket_name,
                'region_name': self.region_name,
                'available_periods_count': len(available_periods),
                'latest_period': available_periods[0] if available_periods else None,
                'oldest_period': available_periods[-1] if available_periods else None,
                'sample_statistics': sample_stats,
                'connection_status': 'connected' if self.test_connection() else 'disconnected'
            }
            
        except Exception as e:
            logger.error(f"統計情報取得エラー: {str(e)}")
            return {
                'error': str(e),
                'connection_status': 'error'
            }


# 設定管理クラス
class S3CommentRepositoryConfig:
    """S3コメントリポジトリの設定管理"""
    
    def __init__(self):
        import os
        
        self.bucket_name = os.getenv('S3_COMMENT_BUCKET', 'it-literacy-457604437098-ap-northeast-1')
        self.region_name = os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-1')
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    def create_repository(self) -> S3CommentRepository:
        """設定からリポジトリインスタンスを作成
        
        Returns:
            S3CommentRepositoryインスタンス
        """
        return S3CommentRepository(
            bucket_name=self.bucket_name,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )


if __name__ == "__main__":
    # テスト用コード
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # リポジトリのテスト
    config = S3CommentRepositoryConfig()
    
    try:
        repo = config.create_repository()
        
        # 接続テスト
        if repo.test_connection():
            print("✅ S3接続成功")
            
            # 利用可能期間の取得
            periods = repo.list_available_periods()
            print(f"📅 利用可能期間: {len(periods)}件")
            
            if periods:
                # 最新期間のデータを少し取得
                latest_period = periods[0]
                collection = repo.fetch_comments_by_period(latest_period)
                print(f"📝 最新期間({latest_period})のコメント: {len(collection.comments)}件")
                
                # 統計情報
                stats = collection.get_statistics()
                print(f"📊 統計情報: {stats}")
                
        else:
            print("❌ S3接続失敗")
            
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
