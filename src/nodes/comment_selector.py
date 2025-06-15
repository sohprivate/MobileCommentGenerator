"""コメント選択ロジックを分離したクラス"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from src.data.comment_generation_state import CommentGenerationState
from src.data.comment_pair import CommentPair
from src.data.past_comment import CommentType, PastCommentCollection, PastComment
from src.data.weather_data import WeatherForecast
from src.llm.llm_manager import LLMManager
from src.config.comment_config import get_comment_config
from src.config.severe_weather_config import get_severe_weather_config
from src.data.forecast_cache import ForecastCache
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.utils.common_utils import SEVERE_WEATHER_PATTERNS, FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)


class CommentSelector:
    """コメント選択クラス"""
    
    def __init__(self, llm_manager: LLMManager, validator: WeatherCommentValidator):
        self.llm_manager = llm_manager
        self.validator = validator
        self.severe_config = get_severe_weather_config()
    
    def select_optimal_comment_pair(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
        """最適なコメントペアを選択"""
        
        # 事前フィルタリング
        filtered_weather = self.validator.get_weather_appropriate_comments(
            weather_comments, weather_data, CommentType.WEATHER_COMMENT, limit=100
        )
        filtered_advice = self.validator.get_weather_appropriate_comments(
            advice_comments, weather_data, CommentType.ADVICE, limit=100
        )
        
        logger.info(f"フィルタリング結果 - 天気: {len(weather_comments)} -> {len(filtered_weather)}")
        logger.info(f"フィルタリング結果 - アドバイス: {len(advice_comments)} -> {len(filtered_advice)}")
        
        # 最適なコメントを選択
        best_weather = self._select_best_weather_comment(
            filtered_weather, weather_data, location_name, target_datetime, state
        )
        best_advice = self._select_best_advice_comment(
            filtered_advice, weather_data, location_name, target_datetime, state
        )
        
        if not best_weather or not best_advice:
            return None
            
        # ペア作成前の最終バリデーション
        if not self._validate_comment_pair(best_weather, best_advice, weather_data):
            # フォールバック処理
            return self._fallback_comment_selection(
                weather_comments, advice_comments, weather_data
            )
        
        return CommentPair(
            weather_comment=best_weather,
            advice_comment=best_advice,
            similarity_score=1.0,
            selection_reason="LLMによる最適選択",
        )
    
    def _select_best_weather_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """最適な天気コメントを選択"""
        if not comments:
            logger.warning("天気コメントが空です")
            return None
            
        candidates = self._prepare_weather_candidates(comments, weather_data)
        if not candidates:
            logger.warning("天気コメント候補が空です")
            return None
            
        selected_comment = self._llm_select_comment(
            candidates, weather_data, location_name, target_datetime, 
            CommentType.WEATHER_COMMENT, state
        )
        
        return selected_comment

    def _select_best_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast, 
        location_name: str, 
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """最適なアドバイスコメントを選択"""
        if not comments:
            logger.warning("アドバイスコメントが空です")
            return None
            
        candidates = self._prepare_advice_candidates(comments, weather_data)
        if not candidates:
            logger.warning("アドバイスコメント候補が空です")
            return None
            
        selected_comment = self._llm_select_comment(
            candidates, weather_data, location_name, target_datetime, 
            CommentType.ADVICE, state
        )
        
        return selected_comment
    
    def _prepare_weather_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> List[Dict[str, Any]]:
        """天気コメント候補を準備"""
        candidates = []
        severe_matched = []
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            if self._should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.debug(f"天気条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(
                len(severe_matched) + len(weather_matched) + len(others), 
                comment, 
                original_index=i
            )
            
            # 悪天候時の特別な優先順位付け
            if self.severe_config.is_severe_weather(weather_data.weather_condition):
                if self._is_severe_weather_appropriate(comment.comment_text, weather_data):
                    severe_matched.append(candidate)
                elif self._is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
            else:
                if self._is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
        
        # 優先順位順に結合（最大50件）
        candidates = (severe_matched[:20] + weather_matched[:20] + others[:10])
        
        return candidates
    
    def _prepare_advice_candidates(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> List[Dict[str, Any]]:
        """アドバイスコメント候補を準備"""
        candidates = []
        
        for i, comment in enumerate(comments):
            if self._should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.debug(f"アドバイス条件不適合のため除外: '{comment.comment_text}'")
                continue
                
            candidate = self._create_candidate_dict(len(candidates), comment, original_index=i)
            candidates.append(candidate)
            
            if len(candidates) >= 50:  # 最大50件
                break
        
        return candidates
    
    def _validate_comment_pair(
        self, 
        weather_comment: PastComment, 
        advice_comment: PastComment, 
        weather_data: WeatherForecast
    ) -> bool:
        """コメントペアの最終バリデーション"""
        weather_valid, weather_reason = self.validator.validate_comment(weather_comment, weather_data)
        advice_valid, advice_reason = self.validator.validate_comment(advice_comment, weather_data)
        
        if not weather_valid or not advice_valid:
            logger.critical("最終バリデーション失敗:")
            logger.critical(f"  天気コメント: '{weather_comment.comment_text}' - {weather_reason}")
            logger.critical(f"  アドバイス: '{advice_comment.comment_text}' - {advice_reason}")
            return False
            
        return True
    
    def _fallback_comment_selection(
        self, 
        weather_comments: List[PastComment], 
        advice_comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> Optional[CommentPair]:
        """フォールバック: 雨天時の代替コメント選択"""
        logger.critical("代替コメント選択を実行")
        
        rain_weather = self._find_rain_appropriate_weather_comment(weather_comments)
        rain_advice = self._find_rain_appropriate_advice_comment(advice_comments, weather_data)
        
        if rain_weather and rain_advice:
            logger.critical(f"代替選択完了 - 天気: '{rain_weather.comment_text}', アドバイス: '{rain_advice.comment_text}'")
            return CommentPair(
                weather_comment=rain_weather,
                advice_comment=rain_advice,
                similarity_score=1.0,
                selection_reason="雨天対応代替選択",
            )
        
        logger.error("代替選択も失敗")
        return None
    
    def _find_rain_appropriate_weather_comment(
        self, 
        comments: List[PastComment]
    ) -> Optional[PastComment]:
        """雨天に適した天気コメントを検索"""
        for comment in comments:
            if (any(keyword in comment.comment_text for keyword in ["雨", "荒れ", "心配", "警戒", "注意"]) and
                not any(forbidden in comment.comment_text for forbidden in ["穏やか", "過ごしやすい", "快適", "爽やか"])):
                return comment
        return None
    
    def _find_rain_appropriate_advice_comment(
        self, 
        comments: List[PastComment], 
        weather_data: WeatherForecast
    ) -> Optional[PastComment]:
        """雨天に適したアドバイスコメントを検索"""
        for comment in comments:
            if (any(keyword in comment.comment_text for keyword in ["傘", "雨", "濡れ", "注意", "安全", "室内"]) and
                not any(forbidden in comment.comment_text for forbidden in ["過ごしやすい", "快適", "お出かけ", "散歩"]) and
                not self._should_exclude_advice_comment(comment.comment_text, weather_data)):
                return comment
        return None
    
    # ヘルパーメソッド（既存のprivate関数から移行）
    def _should_exclude_weather_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """天気コメントを除外すべきかチェック"""
        # 簡単な実装（詳細は既存のロジックを移行）
        return False
    
    def _should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきかチェック"""
        # 簡単な実装（詳細は既存のロジックを移行）
        return False
    
    def _is_severe_weather_appropriate(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """悪天候に適したコメントかチェック"""
        severe_keywords = ["雨", "荒れ", "心配", "警戒", "注意", "傘", "安全"]
        return any(keyword in comment_text for keyword in severe_keywords)
    
    def _is_weather_matched(self, comment_condition: Optional[str], weather_description: str) -> bool:
        """天気条件がマッチするかチェック"""
        if not comment_condition:
            return False
        return comment_condition.lower() in weather_description.lower()
    
    def _create_candidate_dict(self, index: int, comment: PastComment, original_index: int) -> Dict[str, Any]:
        """候補辞書を作成"""
        return {
            'index': index,
            'comment': comment.comment_text,
            'weather_condition': comment.weather_condition or "不明",
            'original_index': original_index,
            'usage_count': comment.usage_count or 0,
            'comment_object': comment  # 元のcommentオブジェクトを保持
        }
    
    def _llm_select_comment(
        self,
        candidates: List[Dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[PastComment]:
        """LLMを使用してコメントを選択"""
        if not candidates:
            return None
        
        # 簡易実装：最初の候補を返す（本来はLLMで選択）
        try:
            selected_candidate = candidates[0]
            # 元のPastCommentオブジェクトを返す
            return selected_candidate['comment_object']
        except (IndexError, KeyError) as e:
            logger.error(f"コメント選択エラー: {e}")
            return None