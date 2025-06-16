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
            # 重複回避のための代替選択を試行
            alternative_pair = self._select_alternative_non_duplicate_pair(
                filtered_weather, filtered_advice, weather_data, location_name, target_datetime, state
            )
            if alternative_pair:
                return alternative_pair
            
            # 代替選択も失敗した場合はフォールバック処理
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
        """コメントペアの最終バリデーション（重複チェック含む）"""
        weather_valid, weather_reason = self.validator.validate_comment(weather_comment, weather_data)
        advice_valid, advice_reason = self.validator.validate_comment(advice_comment, weather_data)
        
        if not weather_valid or not advice_valid:
            logger.critical("最終バリデーション失敗:")
            logger.critical(f"  天気コメント: '{weather_comment.comment_text}' - {weather_reason}")
            logger.critical(f"  アドバイス: '{advice_comment.comment_text}' - {advice_reason}")
            return False
        
        # 重複チェック: 同じ内容の繰り返しを防ぐ
        if self._is_duplicate_content(weather_comment.comment_text, advice_comment.comment_text):
            logger.warning(f"重複コンテンツ検出: 天気='{weather_comment.comment_text}', アドバイス='{advice_comment.comment_text}'")
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
        """天気コメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            from pathlib import Path
            
            # yamlモジュールのインポートを条件付きで実行
            try:
                import yaml
            except ImportError:
                logger.debug("PyYAMLがインストールされていません。基本チェックのみ実行")
                return False
            
            try:
                from src.config.weather_constants import TemperatureThresholds, HumidityThresholds, PrecipitationThresholds
            except ImportError:
                logger.debug("weather_constants.pyが見つかりません。基本チェックのみ実行")
                return False
            
            # YAML設定ファイル読み込み
            config_path = Path(__file__).parent.parent / "config" / "comment_restrictions.yaml"
            if not config_path.exists():
                logger.debug("comment_restrictions.yaml が見つかりません。基本チェックのみ実行")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                restrictions = yaml.safe_load(f)
            
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                if weather_data.precipitation >= PrecipitationThresholds.HEAVY_RAIN:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('weather_comment_forbidden', [])
                else:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('rain', {}).get('weather_comment_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('sunny', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('weather_comment_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でコメント除外: {comment_text}")
                        return True
            
            # 気温による除外チェック
            temp = weather_data.temperature
            temp_restrictions = restrictions.get('temperature_restrictions', {})
            
            if temp >= TemperatureThresholds.HOT_WEATHER:
                forbidden_list = temp_restrictions.get('hot_weather', {}).get('forbidden_keywords', [])
            elif temp < TemperatureThresholds.COLD_COMMENT_THRESHOLD:
                forbidden_list = temp_restrictions.get('cold_weather', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = temp_restrictions.get('mild_weather', {}).get('forbidden_keywords', [])
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"気温条件「{temp}°C」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            # 湿度による除外チェック
            humidity = weather_data.humidity
            humidity_restrictions = restrictions.get('humidity_restrictions', {})
            
            if humidity >= HumidityThresholds.HIGH_HUMIDITY:
                forbidden_list = humidity_restrictions.get('high_humidity', {}).get('forbidden_keywords', [])
            elif humidity < HumidityThresholds.LOW_HUMIDITY:
                forbidden_list = humidity_restrictions.get('low_humidity', {}).get('forbidden_keywords', [])
            else:
                forbidden_list = []
            
            for forbidden in forbidden_list:
                if forbidden in comment_text:
                    logger.debug(f"湿度条件「{humidity}%」で禁止ワード「{forbidden}」によりコメント除外: {comment_text}")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
            return False
    
    def _should_exclude_advice_comment(self, comment_text: str, weather_data: WeatherForecast) -> bool:
        """アドバイスコメントを除外すべきかチェック（YAML設定ベース）"""
        try:
            from pathlib import Path
            
            # yamlモジュールのインポートを条件付きで実行
            try:
                import yaml
            except ImportError:
                logger.debug("PyYAMLがインストールされていません。基本チェックのみ実行")
                return False
            
            try:
                from src.config.weather_constants import PrecipitationThresholds
            except ImportError:
                logger.debug("weather_constants.pyが見つかりません。基本チェックのみ実行")
                return False
            
            # YAML設定ファイル読み込み
            config_path = Path(__file__).parent.parent / "config" / "comment_restrictions.yaml"
            if not config_path.exists():
                logger.debug("comment_restrictions.yaml が見つかりません。基本チェックのみ実行")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                restrictions = yaml.safe_load(f)
            
            # 天気条件による除外チェック
            weather_desc = weather_data.weather_description.lower()
            
            # 雨天時のチェック
            if any(keyword in weather_desc for keyword in ['雨', 'rain']):
                if weather_data.precipitation >= PrecipitationThresholds.HEAVY_RAIN:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('heavy_rain', {}).get('advice_forbidden', [])
                else:
                    forbidden_list = restrictions.get('weather_restrictions', {}).get('rain', {}).get('advice_forbidden', [])
                
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"雨天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 晴天時のチェック
            elif any(keyword in weather_desc for keyword in ['晴', 'clear', 'sunny']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('sunny', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"晴天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            # 曇天時のチェック
            elif any(keyword in weather_desc for keyword in ['曇', 'cloud']):
                forbidden_list = restrictions.get('weather_restrictions', {}).get('cloudy', {}).get('advice_forbidden', [])
                for forbidden in forbidden_list:
                    if forbidden in comment_text:
                        logger.debug(f"曇天時の禁止ワード「{forbidden}」でアドバイス除外: {comment_text}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"YAML設定チェック中にエラー: {e}")
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
        
        # 時系列変化情報を追加（フォールバック戦略付き）
        try:
            from src.data.forecast_cache import ForecastCache
            cache = ForecastCache()
            
            forecast_data_found = False
            
            # 3時間間隔で予報を取得
            forecast_hours = [-12, -6, -3, 3, 6, 12]
            for hours in forecast_hours:
                try:
                    forecast_datetime = target_datetime + timedelta(hours=hours)
                    if forecast_datetime.tzinfo is None and target_datetime.tzinfo is not None:
                        forecast_datetime = forecast_datetime.replace(tzinfo=target_datetime.tzinfo)
                    forecast = cache.get_forecast_at_time(location_name, forecast_datetime)
                    if forecast:
                        forecast_data_found = True
                        if hours < 0:
                            temp_diff = weather_data.temperature - forecast.temperature
                            context += f"- {abs(hours)}時間前: {forecast.temperature}°C ({temp_diff:+.1f}°C差), {forecast.weather_description}\n"
                        else:
                            temp_diff = forecast.temperature - weather_data.temperature
                            context += f"- {hours}時間後: {forecast.temperature}°C ({temp_diff:+.1f}°C変化), {forecast.weather_description}\n"
                except Exception as inner_e:
                    logger.debug(f"{hours}時間後の予報取得エラー: {inner_e}")
                    continue
            
            # フォールバック: 時系列データが取得できない場合の代替情報
            if not forecast_data_found:
                logger.warning("時系列データが取得できませんでした。基本情報のみで判断します。")
                # 季節と現在気温から簡易的な傾向を推定
                month = target_datetime.month
                temp = weather_data.temperature
                
                # 季節的傾向の推定
                if month in [12, 1, 2]:  # 冬
                    if temp > 15:
                        context += "- 冬としては暖かめの気温です\n"
                    elif temp < 5:
                        context += "- 冬らしい寒さです\n"
                elif month in [6, 7, 8]:  # 夏
                    if temp > 30:
                        context += "- 真夏の暑さです\n"
                    elif temp < 25:
                        context += "- 夏としては涼しめです\n"
                elif month in [3, 4, 5]:  # 春
                    context += "- 春らしい気候です\n"
                elif month in [9, 10, 11]:  # 秋
                    context += "- 秋らしい気候です\n"
                
                # 時刻による推定
                hour = target_datetime.hour
                if 6 <= hour <= 10:
                    context += "- 朝の時間帯です\n"
                elif 11 <= hour <= 14:
                    context += "- 昼間の時間帯（気温上昇期）です\n"
                elif 15 <= hour <= 18:
                    context += "- 午後の時間帯です\n"
                else:
                    context += "- 夜間の時間帯（気温下降期）です\n"
                
        except Exception as e:
            logger.warning(f"時系列データ取得で予期しないエラー: {e}")
            # 完全フォールバック: 最小限の情報を追加
            context += "- 時系列データは利用できませんが、現在の気象状況から判断してください\n"
        
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
        """LLMレスポンスから選択インデックスを抽出（堅牢化）"""
        import re
        
        response_clean = response.strip()
        
        # パターン1: 単純な数字のみの回答（最優先）
        if re.match(r'^\d+$', response_clean):
            try:
                index = int(response_clean)
                if 0 <= index < max_index:
                    return index
            except ValueError:
                pass
        
        # パターン2: 行頭の数字（例: "3\n説明文..."）
        match = re.match(r'^(\d+)', response_clean)
        if match:
            try:
                index = int(match.group(1))
                if 0 <= index < max_index:
                    return index
            except ValueError:
                pass
        
        # パターン3: 「答え: 2」「選択: 5」などの形式
        patterns = [
            r'(?:答え|選択|回答|結果)[:：]\s*(\d+)',
            r'(\d+)\s*(?:番|番目)',
            r'インデックス[:：]\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_clean, re.IGNORECASE)
            if match:
                try:
                    index = int(match.group(1))
                    if 0 <= index < max_index:
                        return index
                except ValueError:
                    continue
        
        # パターン4: 最後の手段として最初に見つかった数字（但し範囲内のもの）
        numbers = re.findall(r'\d+', response_clean)
        for num_str in numbers:
            try:
                index = int(num_str)
                if 0 <= index < max_index:
                    logger.warning(f"数値抽出: フォールバック使用 - '{response_clean}' -> {index}")
                    return index
            except ValueError:
                continue
        
        logger.error(f"数値抽出失敗: '{response_clean}' (範囲: 0-{max_index-1})")
        return None
    
    def _is_duplicate_content(self, weather_text: str, advice_text: str) -> bool:
        """天気コメントとアドバイスの重複をチェック"""
        # 基本的な重複パターンをチェック
        
        # 1. 完全一致
        if weather_text == advice_text:
            return True
        
        # 2. 主要キーワードの重複チェック
        # 同じ重要キーワードが両方に含まれている場合は重複と判定
        duplicate_keywords = [
            "にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑",
            "注意", "警戒", "対策", "気をつけ", "備え", "準備"
        ]
        
        weather_keywords = []
        advice_keywords = []
        
        for keyword in duplicate_keywords:
            if keyword in weather_text:
                weather_keywords.append(keyword)
            if keyword in advice_text:
                advice_keywords.append(keyword)
        
        # 3. 重要キーワードが重複している場合
        common_keywords = set(weather_keywords) & set(advice_keywords)
        if common_keywords:
            # 特に以下のキーワードは重複を強く示唆
            critical_duplicates = {"にわか雨", "熱中症", "紫外線", "雷", "強風", "大雨", "猛暑", "酷暑"}
            if any(keyword in critical_duplicates for keyword in common_keywords):
                logger.debug(f"重複キーワード検出: {common_keywords}")
                return True
        
        # 4. 類似表現のチェック
        similarity_patterns = [
            (["雨が心配", "雨に注意"], ["雨", "注意"]),
            (["暑さが心配", "暑さに注意"], ["暑", "注意"]),
            (["風が強い", "風に注意"], ["風", "注意"]),
            (["紫外線が強い", "紫外線対策"], ["紫外線"]),
            (["雷が心配", "雷に注意"], ["雷", "注意"]),
        ]
        
        for weather_patterns, advice_patterns in similarity_patterns:
            weather_match = any(pattern in weather_text for pattern in weather_patterns)
            advice_match = any(pattern in advice_text for pattern in advice_patterns)
            if weather_match and advice_match:
                logger.debug(f"類似表現検出: 天気パターン={weather_patterns}, アドバイスパターン={advice_patterns}")
                return True
        
        # 5. 文字列の類似度チェック（簡易版）
        # 短いコメントで70%以上の文字が共通している場合
        if len(weather_text) <= 10 and len(advice_text) <= 10:
            common_chars = set(weather_text) & set(advice_text)
            max_length = max(len(weather_text), len(advice_text))
            if max_length > 0 and len(common_chars) / max_length > 0.7:
                logger.debug(f"高い文字列類似度検出: {len(common_chars) / max_length:.2f}")
                return True
        
        return False
    
    def _select_alternative_non_duplicate_pair(
        self,
        weather_comments: List[PastComment],
        advice_comments: List[PastComment],
        weather_data: WeatherForecast,
        location_name: str,
        target_datetime: datetime,
        state: Optional[CommentGenerationState] = None
    ) -> Optional[CommentPair]:
        """重複を回避する代替ペア選択"""
        logger.info("重複回避のための代替コメントペア選択を開始")
        
        # 複数の候補を生成して重複しないペアを探す
        weather_candidates = self._prepare_weather_candidates(weather_comments, weather_data)
        advice_candidates = self._prepare_advice_candidates(advice_comments, weather_data)
        
        # 上位候補から順に試行（最大10回）
        max_attempts = min(10, len(weather_candidates), len(advice_candidates))
        
        for attempt in range(max_attempts):
            try:
                # 天気コメント候補を選択（異なるものを順番に試す）
                weather_idx = attempt % len(weather_candidates)
                weather_candidate = weather_candidates[weather_idx]['comment_object']
                
                # アドバイス候補を選択
                advice_idx = attempt % len(advice_candidates)
                advice_candidate = advice_candidates[advice_idx]['comment_object']
                
                # 重複チェック
                if not self._is_duplicate_content(weather_candidate.comment_text, advice_candidate.comment_text):
                    # 個別バリデーション
                    weather_valid, _ = self.validator.validate_comment(weather_candidate, weather_data)
                    advice_valid, _ = self.validator.validate_comment(advice_candidate, weather_data)
                    
                    if weather_valid and advice_valid:
                        logger.info(f"代替ペア選択成功 (試行{attempt+1}): 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                        return CommentPair(
                            weather_comment=weather_candidate,
                            advice_comment=advice_candidate,
                            similarity_score=0.8,  # 代替選択なので若干低めのスコア
                            selection_reason=f"重複回避代替選択（試行{attempt+1}回目）"
                        )
                
                logger.debug(f"試行{attempt+1}: 重複または無効 - 天気='{weather_candidate.comment_text}', アドバイス='{advice_candidate.comment_text}'")
                
            except Exception as e:
                logger.warning(f"代替選択試行{attempt+1}でエラー: {e}")
                continue
        
        logger.warning("重複しない代替ペアの選択に失敗")
        return None