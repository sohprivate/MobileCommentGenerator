"""天気コメント生成ノード

LLMを使用して天気情報と過去コメントを基にコメントを生成する。
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
import yaml

# langgraph nodeデコレータは新バージョンでは不要

from src.data.comment_generation_state import CommentGenerationState
from src.llm.llm_manager import LLMManager
from src.data.weather_data import WeatherForecast
from src.data.comment_pair import CommentPair
from src.config.weather_config import get_config
from src.utils.common_utils import get_season_from_month, get_time_period_from_hour

logger = logging.getLogger(__name__)


async def generate_comment_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    LLMを使用してコメントを生成するノード。

    Args:
        state: 現在のワークフロー状態

    Returns:
        更新された状態（generated_comment追加）
    """
    try:
        print("🔥🔥🔥 GENERATE_COMMENT_NODE CALLED 🔥🔥🔥")
        logger.critical("🔥🔥🔥 GENERATE_COMMENT_NODE CALLED 🔥🔥🔥")
        logger.info("Starting comment generation")

        # 必要なデータの確認
        weather_data = state.weather_data
        selected_pair = state.selected_pair
        llm_provider = state.llm_provider if hasattr(state, 'llm_provider') and state.llm_provider else "openai"

        if not weather_data:
            raise ValueError("Weather data is required for comment generation")

        if not selected_pair:
            raise ValueError("Selected comment pair is required for generation")

        # LLMマネージャーの初期化
        llm_manager = LLMManager(provider=llm_provider)

        # 制約条件の設定
        constraints = {
            "max_length": 15,
            "ng_words": _get_ng_words(),
            "time_period": _get_time_period(state.target_datetime),
            "season": _get_season(state.target_datetime),
        }

        # LLMを使用してコメント生成
        generated_comment = await llm_manager.generate_comment(
            weather_data=weather_data,
            past_comments=selected_pair,
            constraints=constraints
        )
        
        # 選択されたコメントペアから最終コメントを構成
        # S3から選択された天気コメントとアドバイスをそのまま組み合わせる
        weather_comment = (
            selected_pair.weather_comment.comment_text if selected_pair.weather_comment else ""
        )
        advice_comment = (
            selected_pair.advice_comment.comment_text if selected_pair.advice_comment else ""
        )

        # 緊急安全チェック：完全に不適切な組み合わせを強制修正
        logger.critical(f"🚨 最終安全チェック開始: 天気='{weather_data.weather_description}', 気温={weather_data.temperature}°C")
        logger.critical(f"🚨 選択されたコメント: 天気='{weather_comment}', アドバイス='{advice_comment}'")
        
        # 晴天・快晴時の「変わりやすい空」は絶対に不適切 - 既存コメントから再選択
        if any(sunny in weather_data.weather_description for sunny in ["晴", "快晴", "猛暑"]) and weather_comment:
            changeable_patterns = [
                "変わりやすい空", "変わりやすい天気", "変わりやすい",
                "変化しやすい空", "移ろいやすい空", "気まぐれな空", "不安定な空模様"
            ]
            for pattern in changeable_patterns:
                if pattern in weather_comment:
                    logger.critical(f"🚨 緊急修正: 晴天時に「{pattern}」は不適切 - 代替コメント検索")
                    
                    # stateから過去コメントデータを取得して適切なものを選択
                    if hasattr(state, 'past_weather_comments') and getattr(state, 'past_weather_comments', None):
                        # 気温に応じた適切なコメントのパターン
                        if weather_data.temperature >= 35:
                            preferred_patterns = ["猛烈な暑さ", "危険な暑さ", "猛暑に警戒", "激しい暑さ"]
                        elif weather_data.temperature >= 30:
                            preferred_patterns = ["厳しい暑さ", "強い日差し", "厳しい残暑", "強烈な日差し"]
                        else:
                            preferred_patterns = ["爽やかな晴天", "穏やかな空", "心地よい天気", "過ごしやすい天気"]
                        
                        # 既存コメントから適切なものを検索
                        replacement_found = False
                        for past_comment in (getattr(state, 'past_weather_comments', [])):
                            comment_text = past_comment.comment_text
                            # 優先パターンに一致するものを探す
                            for preferred in preferred_patterns:
                                if preferred in comment_text:
                                    weather_comment = comment_text
                                    logger.critical(f"🚨 代替コメント発見: '{weather_comment}'")
                                    replacement_found = True
                                    break
                            if replacement_found:
                                break
                        
                        # 優先パターンが見つからない場合、晴天系の任意のコメントを選択
                        if not replacement_found:
                            sunny_keywords = ["晴", "日差し", "太陽", "快晴", "青空"]
                            for past_comment in (getattr(state, 'past_weather_comments', [])):
                                comment_text = past_comment.comment_text
                                if any(keyword in comment_text for keyword in sunny_keywords) and \
                                   not any(ng in comment_text for ng in changeable_patterns):
                                    weather_comment = comment_text
                                    logger.critical(f"🚨 晴天系代替コメント: '{weather_comment}'")
                                    replacement_found = True
                                    break
                        
                        # それでも見つからない場合はデフォルト（最初の有効なコメント）
                        if not replacement_found and hasattr(state, 'past_weather_comments') and getattr(state, 'past_weather_comments', None):
                            weather_comment = getattr(state, 'past_weather_comments', [])[0].comment_text
                            logger.critical(f"🚨 デフォルト代替: '{weather_comment}'")
                    else:
                        logger.critical("🚨 代替コメントが見つからないため、デフォルト維持")
                    
                    break
        
        # 雨天で熱中症警告は絶対に不適切 - 既存コメントから再選択
        if "雨" in weather_data.weather_description and weather_data.temperature < 30.0 and advice_comment and "熱中症" in advice_comment:
            logger.critical(f"🚨 緊急修正: 雨天+低温で熱中症警告を除外 - 代替アドバイス検索")
            
            if hasattr(state, 'past_advice_comments') and getattr(state, 'past_advice_comments', None):
                # 雨天に適したアドバイスを検索
                rain_patterns = ["雨にご注意", "傘", "濡れ", "雨具", "足元", "滑り"]
                replacement_found = False
                
                for past_comment in (getattr(state, 'past_advice_comments', [])):
                    comment_text = past_comment.comment_text
                    if any(pattern in comment_text for pattern in rain_patterns):
                        advice_comment = comment_text
                        logger.critical(f"🚨 雨天用代替アドバイス: '{advice_comment}'")
                        replacement_found = True
                        break
                
                if not replacement_found and hasattr(state, 'past_advice_comments') and getattr(state, 'past_advice_comments', None):
                    advice_comment = getattr(state, 'past_advice_comments', [])[0].comment_text
                    logger.critical(f"🚨 デフォルト代替アドバイス: '{advice_comment}'")
        
        # 大雨・嵐でムシムシ暑いは不適切 - 既存コメントから再選択
        if ("大雨" in weather_data.weather_description or "嵐" in weather_data.weather_description) and weather_comment and "ムシムシ" in weather_comment:
            logger.critical(f"🚨 緊急修正: 悪天候でムシムシコメントを除外 - 代替コメント検索")
            
            if hasattr(state, 'past_weather_comments') and getattr(state, 'past_weather_comments', None):
                # 悪天候に適したコメントを検索
                storm_patterns = ["荒れた天気", "大雨", "激しい雨", "暴風", "警戒", "注意", "本格的な雨"]
                replacement_found = False
                
                for past_comment in (getattr(state, 'past_weather_comments', [])):
                    comment_text = past_comment.comment_text
                    if any(pattern in comment_text for pattern in storm_patterns):
                        weather_comment = comment_text
                        logger.critical(f"🚨 悪天候用代替コメント: '{weather_comment}'")
                        replacement_found = True
                        break
                
                if not replacement_found and hasattr(state, 'past_weather_comments') and getattr(state, 'past_weather_comments', None):
                    weather_comment = getattr(state, 'past_weather_comments', [])[0].comment_text
                    logger.critical(f"🚨 デフォルト代替: '{weather_comment}'")

        # 最終コメント構成
        if weather_comment and advice_comment:
            generated_comment = f"{weather_comment}　{advice_comment}"
        elif weather_comment:
            generated_comment = weather_comment
        elif advice_comment:
            generated_comment = advice_comment
        else:
            generated_comment = "コメントが選択できませんでした"

        logger.info(f"Final comment (from CSV): {generated_comment}")
        logger.info(f"  - Weather part: {weather_comment}")
        logger.info(f"  - Advice part: {advice_comment}")

        # 状態の更新
        state.generated_comment = generated_comment
        state.update_metadata("llm_provider", llm_provider)
        state.update_metadata("generation_timestamp", datetime.now().isoformat())
        state.update_metadata("constraints_applied", constraints)
        state.update_metadata(
            "selected_past_comments",
            [
                {"type": "weather", "text": weather_comment} if weather_comment else None,
                {"type": "advice", "text": advice_comment} if advice_comment else None,
            ],
        )
        state.update_metadata("comment_source", "S3_PAST_COMMENTS")

        # 気象データをメタデータに追加
        if weather_data:
            state.update_metadata("temperature", weather_data.temperature)
            state.update_metadata("weather_condition", weather_data.weather_description)
            state.update_metadata("humidity", weather_data.humidity)
            state.update_metadata("wind_speed", weather_data.wind_speed)
            
            # 気温差情報をメタデータに追加
            temperature_differences = state.generation_metadata.get("temperature_differences", {})
            if temperature_differences:
                state.update_metadata("previous_day_temperature_diff", temperature_differences.get("previous_day_diff"))
                state.update_metadata("twelve_hours_ago_temperature_diff", temperature_differences.get("twelve_hours_ago_diff"))
                state.update_metadata("daily_temperature_range", temperature_differences.get("daily_range"))
                
                # 気温差の特徴を分析
                temp_diff_analysis = _analyze_temperature_differences(temperature_differences, weather_data.temperature)
                state.update_metadata("temperature_analysis", temp_diff_analysis)

        return state

    except Exception as e:
        logger.error(f"Error in generate_comment_node: {str(e)}")
        state.add_error(str(e), "generate_comment")

        # エラーを再発生させて適切に処理
        raise


def _get_ng_words() -> List[str]:
    """NGワードリストを取得"""
    # 設定ファイルから読み込み
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "ng_words.yaml")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("ng_words", [])
    except FileNotFoundError:
        logger.warning(f"NG words config file not found: {config_path}")
        # フォールバック
        return [
            "災害",
            "危険",
            "注意",
            "警告",
            "絶対",
            "必ず",
            "間違いない",
            "くそ",
            "やばい",
            "最悪",
        ]
    except Exception as e:
        logger.error(f"Error loading NG words config: {e}")
        # フォールバック
        return [
            "災害",
            "危険",
            "注意",
            "警告",
            "絶対",
            "必ず",
            "間違いない",
            "くそ",
            "やばい",
            "最悪",
        ]


def _get_time_period(target_datetime: Optional[datetime]) -> str:
    """時間帯を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    return get_time_period_from_hour(target_datetime.hour)


def _get_season(target_datetime: Optional[datetime]) -> str:
    """季節を判定"""
    if not target_datetime:
        target_datetime = datetime.now()
    return get_season_from_month(target_datetime.month)




def _analyze_temperature_differences(temperature_differences: Dict[str, Optional[float]], current_temp: float) -> Dict[str, Any]:
    """気温差を分析して特徴を抽出
    
    温度差の閾値について：
    - 前日との差 5.0℃: 人体が明確に体感できる温度差として設定。気象学的に「顕著な変化」とされる基準
    - 12時間前との差 3.0℃: 半日での変化として、体調管理に影響する可能性がある基準値
    - 日較差 15.0℃（大）/10.0℃（中）: 健康影響の観点から、15℃以上は要注意、10℃以上は留意すべき差として設定
    
    Args:
        temperature_differences: 気温差の辞書
        current_temp: 現在の気温
        
    Returns:
        気温差の分析結果
    """
    # 設定から閾値を取得
    config = get_config()
    threshold_previous_day = config.weather.temp_diff_threshold_previous_day
    threshold_12hours = config.weather.temp_diff_threshold_12hours
    threshold_daily_large = config.weather.daily_temp_range_threshold_large
    threshold_daily_medium = config.weather.daily_temp_range_threshold_medium
    
    analysis = {
        "has_significant_change": False,
        "change_type": None,
        "change_magnitude": None,
        "commentary": []
    }
    
    try:
        # 前日との比較
        prev_day_diff = temperature_differences.get("previous_day_diff")
        if prev_day_diff is not None:
            if abs(prev_day_diff) >= threshold_previous_day:
                analysis["has_significant_change"] = True
                if prev_day_diff > 0:
                    analysis["change_type"] = "warmer_than_yesterday"
                    analysis["commentary"].append(f"前日より{prev_day_diff:.1f}℃高い")
                else:
                    analysis["change_type"] = "cooler_than_yesterday"
                    analysis["commentary"].append(f"前日より{abs(prev_day_diff):.1f}℃低い")
                
                # 変化の程度を分類
                if abs(prev_day_diff) >= 10.0:
                    analysis["change_magnitude"] = "large"
                elif abs(prev_day_diff) >= 7.0:
                    analysis["change_magnitude"] = "moderate"
                else:
                    analysis["change_magnitude"] = "small"
        
        # 12時間前との比較
        twelve_hours_diff = temperature_differences.get("twelve_hours_ago_diff")
        if twelve_hours_diff is not None:
            if abs(twelve_hours_diff) >= threshold_12hours:
                if twelve_hours_diff > 0:
                    analysis["commentary"].append(f"12時間前より{twelve_hours_diff:.1f}℃上昇")
                else:
                    analysis["commentary"].append(f"12時間前より{abs(twelve_hours_diff):.1f}℃下降")
        
        # 日較差の分析
        daily_range = temperature_differences.get("daily_range")
        if daily_range is not None:
            if daily_range >= threshold_daily_large:
                analysis["commentary"].append(f"日較差が大きい（{daily_range:.1f}℃）")
            elif daily_range >= threshold_daily_medium:
                analysis["commentary"].append(f"やや日較差あり（{daily_range:.1f}℃）")
        
        # 設定から温度閾値を取得
        config = get_config()
        temp_hot = config.weather.temp_threshold_hot
        temp_warm = config.weather.temp_threshold_warm  
        temp_cool = config.weather.temp_threshold_cool
        temp_cold = config.weather.temp_threshold_cold
        
        # 現在の気温レベルに応じたコメント
        if current_temp >= temp_hot:
            analysis["commentary"].append("暑い気温")
        elif current_temp >= temp_warm:
            analysis["commentary"].append("暖かい気温")
        elif current_temp <= temp_cold:
            analysis["commentary"].append("寒い気温")
        elif current_temp <= temp_cool:
            analysis["commentary"].append("涼しい気温")
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"気温差分析中にエラー: {type(e).__name__}: {e}")
    except Exception as e:
        logger.error(f"気温差分析中に予期しないエラー: {type(e).__name__}: {e}", exc_info=True)
    
    return analysis


# エクスポート
__all__ = [
    "generate_comment_node",
    "_get_ng_words",
    "_get_time_period",
    "_get_season",
]
