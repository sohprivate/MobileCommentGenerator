"""コメント選択ロジックを分離したクラス"""

import logging
from datetime import datetime, timedelta
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
        
        # 候補が1つだけの場合は選択の必要なし
        if len(candidates) == 1:
            logger.info(f"候補が1件のみ、そのまま選択: '{candidates[0]['comment']}'")
            return candidates[0]['comment_object']
        
        try:
            logger.info(f"LLM選択開始: {len(candidates)}件の候補から選択中...")
            
            # LLMによる選択を実行
            selected_candidate = self._perform_llm_selection(
                candidates, weather_data, location_name, target_datetime, comment_type
            )
            
            if selected_candidate:
                logger.info(f"LLMによる選択完了: '{selected_candidate['comment']}' (インデックス: {selected_candidate['index']})")
                return selected_candidate['comment_object']
            else:
                # LLM選択に失敗した場合は最初の候補を返す
                logger.warning("LLM選択に失敗、最初の候補を使用")
                logger.warning(f"フォールバック選択: '{candidates[0]['comment']}'")
                return candidates[0]['comment_object']
                
        except Exception as e:
            logger.error(f"LLM選択エラー: {e}")
            # エラー時は最初の候補を返す
            return candidates[0]['comment_object']
    
    def _perform_llm_selection(
        self,
        candidates: List[Dict[str, Any]],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        comment_type: CommentType
    ) -> Optional[Dict[str, Any]]:
        """LLMによる実際の選択処理"""
        # 候補リストを文字列として整形
        candidates_text = self._format_candidates_for_llm(candidates)
        
        # 天気情報を整形
        weather_context = self._format_weather_context(weather_data, location_name, target_datetime)
        
        # コメントタイプ別のプロンプトを作成
        prompt = self._create_selection_prompt(candidates_text, weather_context, comment_type)
        
        try:
            logger.info(f"LLMに選択プロンプトを送信中...")
            logger.debug(f"プロンプト内容: {prompt[:200]}...")
            
            # LLMに選択を依頼
            response = self.llm_manager.generate(prompt)
            
            logger.info(f"LLMレスポンス: {response}")
            
            # レスポンスから選択されたインデックスを抽出
            selected_index = self._extract_selected_index(response, len(candidates))
            
            logger.info(f"抽出されたインデックス: {selected_index}")
            
            if selected_index is not None and 0 <= selected_index < len(candidates):
                return candidates[selected_index]
            else:
                logger.warning(f"無効な選択インデックス: {selected_index}")
                return None
                
        except Exception as e:
            logger.error(f"LLM API呼び出しエラー: {e}")
            return None
    
    def _format_candidates_for_llm(self, candidates: List[Dict[str, Any]]) -> str:
        """候補をLLM用に整形"""
        formatted_candidates = []
        for i, candidate in enumerate(candidates):
            formatted_candidates.append(
                f"{i}: {candidate['comment']} "
                f"(天気条件: {candidate['weather_condition']}, 使用回数: {candidate['usage_count']})"
            )
        return "\n".join(formatted_candidates)
    
    def _format_weather_context(self, weather_data: WeatherForecast, location_name: str, target_datetime: datetime) -> str:
        """天気情報をLLM用に整形（時系列分析を含む）"""
        
        # 基本天気情報
        context = f"""
現在の天気情報:
- 場所: {location_name}
- 日時: {target_datetime.strftime('%Y年%m月%d日 %H時')}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 降水量: {weather_data.precipitation}mm
- 風速: {weather_data.wind_speed}m/s
"""
        
        # 時系列変化情報を追加（stateから取得可能な場合）
        try:
            from src.data.forecast_cache import ForecastCache
            cache = ForecastCache()
            
            # 3時間間隔で予報を取得
            forecast_hours = [-12, -6, -3, 3, 6, 12]
            for hours in forecast_hours:
                forecast_datetime = target_datetime + timedelta(hours=hours)
                if forecast_datetime.tzinfo is None and target_datetime.tzinfo is not None:
                    forecast_datetime = forecast_datetime.replace(tzinfo=target_datetime.tzinfo)
                forecast = cache.get_forecast_at_time(location_name, forecast_datetime)
                if forecast:
                    if hours < 0:
                        temp_diff = weather_data.temperature - forecast.temperature
                        context += f"- {abs(hours)}時間前: {forecast.temperature}°C ({temp_diff:+.1f}°C差), {forecast.weather_description}\n"
                    else:
                        temp_diff = forecast.temperature - weather_data.temperature
                        context += f"- {hours}時間後: {forecast.temperature}°C ({temp_diff:+.1f}°C変化), {forecast.weather_description}\n"
                
        except Exception as e:
            logger.debug(f"時系列データ取得エラー: {e}")
        
        return context
    
    def _create_selection_prompt(self, candidates_text: str, weather_context: str, comment_type: CommentType) -> str:
        """選択用プロンプトを作成"""
        comment_type_desc = "天気コメント" if comment_type == CommentType.WEATHER_COMMENT else "アドバイスコメント"
        
        return f"""
以下の天気情報と時系列変化を総合的に分析し、最も適した{comment_type_desc}を選択してください。

{weather_context}

候補一覧:
{candidates_text}

選択基準（重要度順）:
1. 現在の天気・気温に最も適している
2. 時系列変化（12時間前後）を考慮した適切性
3. 地域特性（北海道の寒さ、沖縄の暑さなど）
4. 季節感が適切
5. 自然で読みやすい表現

特に以下を重視してください:
- 気温変化の傾向（上昇中、下降中、安定）
- 天気の変化予想（悪化、改善、安定）
- その地域の気候特性

【重要】選択した候補の番号のみを回答してください。
説明は不要です。数字のみを返してください。

例: 2
"""
    
    def _extract_selected_index(self, response: str, max_index: int) -> Optional[int]:
        """LLMレスポンスから選択インデックスを抽出"""
        import re
        
        # 数字のみを抽出
        numbers = re.findall(r'\d+', response.strip())
        
        if numbers:
            try:
                index = int(numbers[0])
                if 0 <= index < max_index:
                    return index
            except ValueError:
                pass
        
        return None