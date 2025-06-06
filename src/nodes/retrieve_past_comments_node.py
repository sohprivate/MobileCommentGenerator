"""
過去コメント取得ノード

LangGraphノードとしてS3から過去コメントを取得し、
現在の天気状況に基づいて関連コメントを検索する
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.data.past_comment import PastComment, PastCommentCollection, CommentType
from src.repositories.s3_comment_repository import S3CommentRepository, S3CommentRepositoryConfig, S3CommentRepositoryError


# ログ設定
logger = logging.getLogger(__name__)


class RetrievePastCommentsNode:
    """過去コメント取得ノード
    
    LangGraphワークフローで使用される過去コメント取得機能
    """
    
    def __init__(self, repository: Optional[S3CommentRepository] = None):
        """過去コメント取得ノードを初期化
        
        Args:
            repository: S3コメントリポジトリ（Noneの場合は自動作成）
        """
        if repository is None:
            config = S3CommentRepositoryConfig()
            self.repository = config.create_repository()
        else:
            self.repository = repository
        
        # ノード設定
        self.default_months_back = 6  # デフォルト検索期間
        self.max_comments_per_type = 10  # タイプごとの最大コメント数
        self.min_similarity_threshold = 0.3  # 最小類似度閾値
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """ノード実行メイン関数
        
        Args:
            state: LangGraphの状態辞書
                必要なキー:
                - location_name: 地点名
                - weather_data: 天気予報データ（オプション）
                - target_datetime: 対象日時（オプション）
                
        Returns:
            更新された状態辞書
                追加されるキー:
                - past_comments: 取得された過去コメントリスト
                - comment_retrieval_metadata: 取得処理のメタデータ
        """
        try:
            logger.info("過去コメント取得ノード開始")
            
            # 入力パラメータの抽出
            location_name = state.get('location_name')
            weather_data = state.get('weather_data')
            target_datetime = state.get('target_datetime', datetime.now())
            
            if not location_name:
                raise ValueError("location_name が指定されていません")
            
            # 天気情報の抽出
            weather_condition = None
            temperature = None
            
            if weather_data:
                weather_condition = self._extract_weather_condition(weather_data)
                temperature = self._extract_temperature(weather_data)
            
            # 過去コメントの検索・取得
            past_comments = self._retrieve_past_comments(
                location_name=location_name,
                weather_condition=weather_condition,
                temperature=temperature,
                target_datetime=target_datetime
            )
            
            # メタデータの生成
            metadata = self._generate_metadata(past_comments, location_name, weather_condition)
            
            # 状態の更新
            updated_state = state.copy()
            updated_state['past_comments'] = [c.to_dict() for c in past_comments]
            updated_state['comment_retrieval_metadata'] = metadata
            
            logger.info(f"過去コメント取得完了: {len(past_comments)}件")
            return updated_state
            
        except Exception as e:
            logger.error(f"過去コメント取得エラー: {str(e)}")
            
            # エラー時も処理を継続できるよう空のデータを返す
            error_state = state.copy()
            error_state['past_comments'] = []
            error_state['comment_retrieval_metadata'] = {
                'error': str(e),
                'total_comments': 0,
                'retrieval_successful': False
            }
            return error_state
    
    def _extract_weather_condition(self, weather_data: Dict[str, Any]) -> Optional[str]:
        """天気データから天気状況を抽出
        
        Args:
            weather_data: 天気データ辞書
            
        Returns:
            天気状況文字列
        """
        # 複数の可能なキーを試行
        possible_keys = [
            'weather_description',
            'weather_condition', 
            'condition',
            'description',
            'weather'
        ]
        
        for key in possible_keys:
            if key in weather_data and weather_data[key]:
                return str(weather_data[key])
        
        # ネストされた構造の場合
        if 'current_weather' in weather_data:
            current = weather_data['current_weather']
            if isinstance(current, dict):
                for key in possible_keys:
                    if key in current and current[key]:
                        return str(current[key])
        
        logger.warning("天気状況を抽出できませんでした")
        return None
    
    def _extract_temperature(self, weather_data: Dict[str, Any]) -> Optional[float]:
        """天気データから気温を抽出
        
        Args:
            weather_data: 天気データ辞書
            
        Returns:
            気温（℃）
        """
        # 複数の可能なキーを試行
        possible_keys = ['temperature', 'temp', 'current_temperature']
        
        for key in possible_keys:
            if key in weather_data and weather_data[key] is not None:
                try:
                    return float(weather_data[key])
                except (ValueError, TypeError):
                    continue
        
        # ネストされた構造の場合
        if 'current_weather' in weather_data:
            current = weather_data['current_weather']
            if isinstance(current, dict):
                for key in possible_keys:
                    if key in current and current[key] is not None:
                        try:
                            return float(current[key])
                        except (ValueError, TypeError):
                            continue
        
        logger.warning("気温を抽出できませんでした")
        return None
    
    def _retrieve_past_comments(
        self,
        location_name: str,
        weather_condition: Optional[str] = None,
        temperature: Optional[float] = None,
        target_datetime: Optional[datetime] = None
    ) -> List[PastComment]:
        """過去コメントを取得
        
        Args:
            location_name: 地点名
            weather_condition: 天気状況
            temperature: 気温
            target_datetime: 対象日時
            
        Returns:
            過去コメントのリスト
        """
        try:
            if weather_condition:
                # 類似天気状況のコメントを検索
                similar_comments = self.repository.search_similar_comments(
                    target_weather_condition=weather_condition,
                    target_temperature=temperature,
                    target_location=location_name,
                    months_back=self.default_months_back,
                    max_results=self.max_comments_per_type * 2,
                    min_similarity=self.min_similarity_threshold
                )
                
                if similar_comments:
                    logger.info(f"類似天気での検索: {len(similar_comments)}件見つかりました")
                    return self._balance_comment_types(similar_comments)
            
            # フォールバック: 地点のみで検索
            logger.info(f"地点のみでの検索: {location_name}")
            location_collection = self.repository.get_recent_comments(
                months_back=self.default_months_back,
                location=location_name,
                max_comments=self.max_comments_per_type * 2
            )
            
            if location_collection.comments:
                return self._balance_comment_types(location_collection.comments)
            
            # 最終フォールバック: 全体から最近のコメント
            logger.info("全体からの最近コメント取得")
            general_collection = self.repository.get_recent_comments(
                months_back=self.default_months_back // 2,
                max_comments=self.max_comments_per_type
            )
            
            return general_collection.comments[:self.max_comments_per_type]
            
        except S3CommentRepositoryError as e:
            logger.error(f"S3からのコメント取得エラー: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"コメント取得エラー: {str(e)}")
            return []
    
    def _balance_comment_types(self, comments: List[PastComment]) -> List[PastComment]:
        """コメントタイプのバランスを調整
        
        Args:
            comments: 元のコメントリスト
            
        Returns:
            タイプバランス調整後のコメントリスト
        """
        # タイプ別に分類
        weather_comments = []
        advice_comments = []
        other_comments = []
        
        for comment in comments:
            if comment.comment_type == CommentType.WEATHER_COMMENT:
                weather_comments.append(comment)
            elif comment.comment_type == CommentType.ADVICE:
                advice_comments.append(comment)
            else:
                other_comments.append(comment)
        
        # バランス調整
        balanced_comments = []
        max_per_type = self.max_comments_per_type // 2
        
        # 天気コメントを追加
        balanced_comments.extend(weather_comments[:max_per_type])
        
        # アドバイスコメントを追加
        balanced_comments.extend(advice_comments[:max_per_type])
        
        # 残り枠があれば他のコメントを追加
        remaining_slots = self.max_comments_per_type - len(balanced_comments)
        if remaining_slots > 0:
            balanced_comments.extend(other_comments[:remaining_slots])
        
        logger.info(f"コメントタイプバランス調整: 天気{len(weather_comments[:max_per_type])}件, "
                   f"アドバイス{len(advice_comments[:max_per_type])}件, "
                   f"その他{min(remaining_slots, len(other_comments))}件")
        
        return balanced_comments
    
    def _generate_metadata(
        self,
        comments: List[PastComment],
        location: str,
        weather_condition: Optional[str]
    ) -> Dict[str, Any]:
        """取得処理のメタデータを生成
        
        Args:
            comments: 取得されたコメント
            location: 検索地点
            weather_condition: 検索天気状況
            
        Returns:
            メタデータ辞書
        """
        # タイプ別統計
        type_counts = {}
        for comment_type in CommentType:
            count = sum(1 for c in comments if c.comment_type == comment_type)
            type_counts[comment_type.value] = count
        
        # 文字数統計
        char_counts = [len(c.comment_text) for c in comments]
        
        return {
            'total_comments': len(comments),
            'search_location': location,
            'search_weather_condition': weather_condition,
            'type_distribution': type_counts,
            'character_stats': {
                'min_length': min(char_counts) if char_counts else 0,
                'max_length': max(char_counts) if char_counts else 0,
                'avg_length': sum(char_counts) / len(char_counts) if char_counts else 0,
                'within_15_chars': sum(1 for c in char_counts if c <= 15)
            },
            'retrieval_successful': True,
            'retrieval_timestamp': datetime.now().isoformat()
        }


# LangGraphノード関数（従来のスタイル）
def retrieve_past_comments_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraphノード関数
    
    Args:
        state: LangGraphの状態辞書
        
    Returns:
        更新された状態辞書
    """
    node = RetrievePastCommentsNode()
    return node(state)


# 単体使用可能な関数
async def retrieve_past_comments_for_condition(
    location_name: str,
    weather_condition: Optional[str] = None,
    temperature: Optional[float] = None,
    max_comments: int = 10
) -> List[Dict[str, Any]]:
    """指定条件での過去コメント取得（単体使用可能）
    
    Args:
        location_name: 地点名
        weather_condition: 天気状況
        temperature: 気温
        max_comments: 最大コメント数
        
    Returns:
        過去コメントの辞書リスト
    """
    node = RetrievePastCommentsNode()
    node.max_comments_per_type = max_comments
    
    state = {
        'location_name': location_name,
        'weather_data': {
            'weather_condition': weather_condition,
            'temperature': temperature
        } if weather_condition else None
    }
    
    result = node(state)
    return result.get('past_comments', [])


if __name__ == "__main__":
    # テスト用コード
    import asyncio
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_retrieve_node():
        """ノードのテスト"""
        print("=== 過去コメント取得ノードテスト ===")
        
        # テスト状態の作成
        test_state = {
            'location_name': '東京',
            'weather_data': {
                'weather_condition': '晴れ',
                'temperature': 20.0
            },
            'target_datetime': datetime.now()
        }
        
        try:
            # ノード実行
            node = RetrievePastCommentsNode()
            result = node(test_state)
            
            print(f"✅ ノード実行成功")
            print(f"取得コメント数: {len(result.get('past_comments', []))}")
            
            metadata = result.get('comment_retrieval_metadata', {})
            print(f"メタデータ: {metadata}")
            
            # 個別コメントの表示（最初の3件）
            comments = result.get('past_comments', [])
            for i, comment in enumerate(comments[:3]):
                print(f"コメント{i+1}: {comment.get('comment_text', '')} "
                      f"({comment.get('comment_type', '')}, {comment.get('location', '')})")
            
        except Exception as e:
            print(f"❌ テストエラー: {str(e)}")
    
    # 非同期テスト実行
    asyncio.run(test_retrieve_node())
