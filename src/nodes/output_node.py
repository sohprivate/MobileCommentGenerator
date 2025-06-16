"""
出力ノード

最終結果を整形してJSON形式で出力するLangGraphノード
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json

from src.data.comment_generation_state import CommentGenerationState
from src.data.forecast_cache import ForecastCache

logger = logging.getLogger(__name__)


def _get_weather_timeline(location_name: str, base_datetime: datetime) -> Dict[str, Any]:
    """翌日9:00-18:00の天気データを取得
    
    Args:
        location_name: 地点名
        base_datetime: 選択された予報時刻（使用しないが互換性のため維持）
        
    Returns:
        翌日9:00-18:00の時系列天気データ
    """
    from src.data.forecast_cache import ensure_jst
    import pytz
    
    jst = pytz.timezone("Asia/Tokyo")
    now_jst = datetime.now(jst)
    
    timeline_data: Dict[str, Any] = {
        "future_forecasts": [],
        "past_forecasts": [],
        "base_time": base_datetime.isoformat()
    }
    
    try:
        cache = ForecastCache()
        
        # 常に翌日を対象にする
        target_date = now_jst.date() + timedelta(days=1)
        target_hours = [9, 12, 15, 18]
        
        logger.info(f"翌日({target_date})の予報データを取得中: {target_hours}")
        
        for hour in target_hours:
            target_time = jst.localize(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            
            try:
                forecast = cache.get_forecast_at_time(location_name, target_time)
                if forecast:
                    timeline_data["future_forecasts"].append({
                        "time": target_time.strftime("%m/%d %H:%M"),
                        "label": f"{hour:02d}:00",
                        "weather": forecast.weather_description,
                        "temperature": forecast.temperature,
                        "precipitation": forecast.precipitation
                    })
                    logger.debug(f"翌日予報取得成功: {hour:02d}:00 at {target_time}")
                else:
                    logger.warning(f"翌日予報データなし: {hour:02d}:00 at {target_time}")
            except Exception as e:
                logger.warning(f"翌日予報取得エラー ({hour:02d}:00): {e}")
        
        # 過去データ表示は削除（翌日の予報のみ表示）
        timeline_data["past_forecasts"] = []
        
        # データが取得できた場合のみ統計情報を追加
        all_forecasts = timeline_data["future_forecasts"] + timeline_data["past_forecasts"]
        if all_forecasts:
            temps = [f["temperature"] for f in all_forecasts if f["temperature"] is not None]
            precipitations = [f["precipitation"] for f in all_forecasts if f["precipitation"] is not None]
            
            timeline_data["summary"] = {
                "temperature_range": f"{min(temps):.1f}°C〜{max(temps):.1f}°C" if temps else "データなし",
                "max_precipitation": f"{max(precipitations):.1f}mm" if precipitations else "0mm",
                "weather_pattern": _analyze_weather_pattern(all_forecasts)
            }
    
    except Exception as e:
        logger.error(f"天気タイムライン取得エラー: {e}")
        timeline_data["error"] = str(e)
    
    return timeline_data


def _analyze_weather_pattern(forecasts: List[Dict[str, Any]]) -> str:
    """天気パターンを分析
    
    Args:
        forecasts: 予報データのリスト
        
    Returns:
        天気パターンの説明
    """
    if not forecasts:
        return "データなし"
    
    weather_conditions = [f["weather"] for f in forecasts if f["weather"]]
    
    # 悪天候の検出
    severe_conditions = ["大雨", "嵐", "雷", "豪雨", "暴風", "台風"]
    rain_conditions = ["雨", "小雨", "中雨"]
    
    has_severe = any(any(severe in weather for severe in severe_conditions) for weather in weather_conditions)
    has_rain = any(any(rain in weather for rain in rain_conditions) for weather in weather_conditions)
    
    if has_severe:
        return "悪天候注意"
    elif has_rain:
        return "雨天続く"
    elif len(set(weather_conditions)) <= 2:
        return "安定した天気"
    else:
        return "変わりやすい天気"


def output_node(state: CommentGenerationState) -> CommentGenerationState:
    """
    最終結果をJSON形式で出力

    Args:
        state: ワークフローの状態

    Returns:
        出力形式に整形された状態
    """
    logger.info("OutputNode: 出力処理を開始")

    try:
        # 実行時間の計算
        execution_start = state.generation_metadata.get("execution_start_time")
        execution_end = datetime.now()
        execution_time_ms = 0

        if execution_start:
            # execution_startが文字列の場合はdatetimeに変換
            if isinstance(execution_start, str):
                try:
                    execution_start = datetime.fromisoformat(execution_start.replace("Z", "+00:00"))
                except:
                    execution_start = None

            # datetime型の場合のみ計算
            if isinstance(execution_start, datetime):
                execution_time_delta = execution_end - execution_start
                execution_time_ms = int(execution_time_delta.total_seconds() * 1000)

        # 最終コメントの確定
        final_comment = _determine_final_comment(state)
        state.final_comment = final_comment

        # メタデータの生成
        generation_metadata = _create_generation_metadata(state, execution_time_ms)
        state.generation_metadata = generation_metadata

        # 出力データの構築
        output_data = {"final_comment": final_comment, "generation_metadata": generation_metadata}

        # オプション情報の追加
        if state.generation_metadata.get("include_debug_info", False):
            output_data["debug_info"] = _create_debug_info(state)

        # JSON形式への変換
        state.update_metadata("output_json", json.dumps(output_data, ensure_ascii=False, indent=2))

        # 成功ログ
        location_info = f"location={state.location_name}" if state.location_name else "location=unknown"
        logger.info(
            f"出力処理完了: {location_info}, "
            f"comment_length={len(final_comment)}, "
            f"execution_time={execution_time_ms}ms, "
            f"retry_count={state.retry_count}"
        )

        # クリーンアップ
        _cleanup_state(state)

        state.update_metadata("output_processed", True)

    except Exception as e:
        logger.error(f"出力処理中にエラー: {str(e)}")
        state.errors = state.errors + [f"OutputNode: {str(e)}"]
        state.update_metadata("output_processed", False)

        # エラー時の出力
        state.update_metadata(
            "output_json",
            json.dumps(
                {
                    "error": str(e),
                    "final_comment": None,
                    "generation_metadata": {
                        "error": str(e),
                        "execution_time_ms": 0,
                        "errors": state.errors,
                    },
                },
                ensure_ascii=False,
            ),
        )

    return state


def _determine_final_comment(state: CommentGenerationState) -> str:
    """
    最終コメントを確定

    優先順位:
    1. generated_comment（LLM生成）
    2. selected_pair の weather_comment
    3. エラーを発生させる
    """
    logger.debug("最終コメント確定処理開始")
    logger.debug(f"state.generated_comment = '{getattr(state, 'generated_comment', None)}'")
    logger.debug(f"state.selected_pair = {getattr(state, 'selected_pair', None)}")
    
    # 最終安全チェック用データ
    weather_data = state.weather_data
    final_comment = None
    
    # LLM生成コメントがある場合
    if state.generated_comment:
        final_comment = state.generated_comment
        logger.info(f"LLM生成コメント使用: '{final_comment}'")
    else:
        # 選択されたペアがある場合 - 正しい形式で構成
        selected_pair = state.selected_pair
        if selected_pair:
            weather_comment = ""
            advice_comment = ""
            
            if hasattr(selected_pair, "weather_comment") and selected_pair.weather_comment:
                weather_comment = selected_pair.weather_comment.comment_text
                
            if hasattr(selected_pair, "advice_comment") and selected_pair.advice_comment:
                advice_comment = selected_pair.advice_comment.comment_text
            
            logger.debug(f"選択されたペア: weather='{weather_comment}', advice='{advice_comment}'")
            
            # 正しい形式で結合（weather + 全角スペース + advice）
            if weather_comment and advice_comment:
                final_comment = f"{weather_comment}　{advice_comment}"
                logger.info(f"ペア結合コメント使用: '{final_comment}'")
            elif weather_comment:
                final_comment = weather_comment
                logger.info(f"天気コメントのみ使用: '{final_comment}'")
            elif advice_comment:
                final_comment = advice_comment
                logger.info(f"アドバイスコメントのみ使用: '{final_comment}'")

    if not final_comment:
        # コメントが生成できなかった場合はエラー
        raise ValueError(
            "コメントの生成に失敗しました。LLMまたは過去データから適切なコメントを取得できませんでした。"
        )
    
    # 🚨 最終安全チェック：特殊気象条件に対する不適切なコメント組み合わせの修正
    if weather_data and final_comment:
        current_weather = weather_data.weather_description.lower()
        temperature = weather_data.temperature if hasattr(weather_data, 'temperature') else 20.0
        weather_condition = weather_data.weather_condition.value
        
        # 特殊気象条件ごとの文脈保持型安全性チェック
        if weather_condition == "thunder" or "雷" in current_weather:
            logger.info(f"雷天候検出: '{final_comment}'")
            if "　" in final_comment:
                parts = final_comment.split("　")
                # 文脈を保持しながら安全性を確保
                if not any(word in final_comment for word in ["雷", "屋内", "危険", "注意"]):
                    # アドバイス部分に安全情報を追加
                    parts[1] = f"{parts[1]}（雷注意・屋内へ）"
                    final_comment = "　".join(parts)
                    logger.info(f"雷天候安全性強化: '{final_comment}'")
                
        elif weather_condition == "fog" or "霧" in current_weather:
            logger.info(f"霧天候検出: '{final_comment}'")
            if "　" in final_comment:
                parts = final_comment.split("　")
                if not any(word in final_comment for word in ["霧", "視界", "運転", "注意"]):
                    # 文脈を保持して視界注意を追加
                    parts[1] = f"{parts[1]}（視界注意）"
                    final_comment = "　".join(parts)
                    logger.info(f"霧天候安全性強化: '{final_comment}'")
                
        elif weather_condition in ["storm", "severe_storm"] or any(word in current_weather for word in ["嵐", "暴風"]):
            logger.info(f"嵐天候検出: '{final_comment}'")
            if "　" in final_comment:
                parts = final_comment.split("　")
                if not any(word in final_comment for word in ["嵐", "暴風", "強風", "危険"]):
                    # 文脈を保持して強風注意を追加
                    parts[1] = f"{parts[1]}（強風危険・外出注意）"
                    final_comment = "　".join(parts)
                    logger.info(f"嵐天候安全性強化: '{final_comment}'")
                
        elif weather_condition == "heavy_rain" or "大雨" in current_weather:
            logger.info(f"大雨天候検出: '{final_comment}'")
            if "　" in final_comment:
                parts = final_comment.split("　")
                if not any(word in final_comment for word in ["大雨", "洪水", "冠水", "危険"]):
                    # 文脈を保持して大雨注意を追加
                    parts[1] = f"{parts[1]}（大雨・冠水注意）"
                    final_comment = "　".join(parts)
                    logger.info(f"大雨天候安全性強化: '{final_comment}'")
                
        # 雨天で不適切なコメント全般の修正（文脈保持版）
        elif "雨" in current_weather:
            logger.info(f"雨天コメント検証: '{final_comment}'")
            
            inappropriate_keywords = ["熱中症", "暑い", "ムシムシ", "花粉", "日焼け", "紫外線", "散歩", "ピクニック", "外遊び"]
            needs_correction = any(keyword in final_comment for keyword in inappropriate_keywords)
            
            if needs_correction:
                logger.info(f"雨天不適切コメント検出: '{final_comment}'")
                
                if "　" in final_comment:  # 複合コメントの場合
                    parts = final_comment.split("　")
                    
                    # 文脈を保持しながら安全な修正（単語境界考慮）
                    if any(word in parts[0] for word in inappropriate_keywords):
                        # 安全な単語置換（前後の文字を考慮）
                        import re
                        weather_part = parts[0]
                        
                        # 完全一致または単語境界での置換
                        if re.search(r'\b熱中症\b', weather_part):
                            weather_part = re.sub(r'\b熱中症\b', '雨模様', weather_part)
                        if re.search(r'\b暑い\b', weather_part):
                            weather_part = re.sub(r'\b暑い\b', '涼しい', weather_part)
                        if re.search(r'\bムシムシ\b', weather_part):
                            weather_part = re.sub(r'\bムシムシ\b', 'しっとり', weather_part)
                        if re.search(r'\b花粉\b', weather_part):
                            weather_part = re.sub(r'\b花粉\b', '雨', weather_part)
                        
                        # 日焼け・紫外線関連の慎重な置換
                        for keyword in ["日焼け", "紫外線"]:
                            pattern = rf'\b{re.escape(keyword)}\b'
                            if re.search(pattern, weather_part):
                                weather_part = re.sub(pattern, '雨', weather_part)
                        
                        parts[0] = weather_part
                    
                    # アドバイス部分も安全な修正
                    if any(word in parts[1] for word in inappropriate_keywords):
                        import re
                        advice_part = parts[1]
                        
                        # 外出活動の安全な置換
                        if re.search(r'\b散歩\b', advice_part):
                            advice_part = re.sub(r'\b散歩\b', '室内活動', advice_part)
                            advice_part = f"{advice_part}（雨天のため）"
                        elif re.search(r'\bピクニック\b', advice_part):
                            advice_part = re.sub(r'\bピクニック\b', '屋内', advice_part)
                            advice_part = f"{advice_part}（雨天のため）"
                        elif re.search(r'\b外遊び\b', advice_part):
                            advice_part = re.sub(r'\b外遊び\b', '室内遊び', advice_part)
                            advice_part = f"{advice_part}（雨天のため）"
                        elif any(re.search(rf'\b{word}\b', advice_part) for word in ["熱中症", "暑い", "ムシムシ"]):
                            advice_part = "傘をお忘れなく"
                        else:
                            advice_part = f"{advice_part}（雨にご注意）"
                        
                        parts[1] = advice_part
                    
                    final_comment = "　".join(parts)
                else:
                    # 単体コメントは最小限の調整
                    final_comment = f"{final_comment}（雨天注意）"
                
                logger.info(f"雨天修正後: '{final_comment}'")
            
    logger.info(f"最終コメント確定: '{final_comment}'")
    return final_comment


def _create_generation_metadata(
    state: CommentGenerationState, execution_time_ms: int
) -> Dict[str, Any]:
    """
    生成メタデータを作成
    """
    metadata = {
        "execution_time_ms": execution_time_ms,
        "retry_count": state.retry_count,
        "request_id": state.generation_metadata.get("execution_context", {}).get(
            "request_id", "unknown"
        ),
        "generation_timestamp": datetime.now().isoformat(),
        "location_name": state.location_name,
        "target_datetime": state.target_datetime.isoformat() if state.target_datetime else None,
        "llm_provider": state.llm_provider or "none",
    }

    # 天気情報の追加
    weather_data = state.weather_data
    if weather_data:
        weather_info = {}
        
        # 天気状況（有効な値のみ追加）
        weather_condition = getattr(weather_data, "weather_description", None)
        if weather_condition and weather_condition != "不明":
            weather_info["weather_condition"] = weather_condition
        
        # 気温（有効な値のみ追加）
        temperature = getattr(weather_data, "temperature", None)
        if temperature is not None:
            weather_info["temperature"] = temperature
        
        # 湿度（有効な値のみ追加）
        humidity = getattr(weather_data, "humidity", None)
        if humidity is not None:
            weather_info["humidity"] = humidity
        
        # 風速（有効な値のみ追加）
        wind_speed = getattr(weather_data, "wind_speed", None)
        if wind_speed is not None:
            weather_info["wind_speed"] = wind_speed
        
        # 天気データの時刻（予報時刻）
        weather_datetime = getattr(weather_data, "datetime", None)
        if weather_datetime is not None:
            weather_info["weather_forecast_time"] = weather_datetime.isoformat()
            
            # 時系列の天気データを追加
            location_name = state.location_name
            if location_name:
                try:
                    timeline_data = _get_weather_timeline(location_name, weather_datetime)
                    weather_info["weather_timeline"] = timeline_data
                    logger.info(f"時系列データを追加: 過去{len(timeline_data.get('past_forecasts', []))}件、未来{len(timeline_data.get('future_forecasts', []))}件")
                except Exception as e:
                    logger.warning(f"時系列データ取得エラー: {e}")
                    weather_info["weather_timeline"] = {"error": str(e)}
        
        # 有効な天気データがある場合のみ追加
        if weather_info:
            metadata.update(weather_info)

    # 選択されたコメント情報
    selected_pair = state.selected_pair
    if selected_pair:
        metadata["selected_past_comments"] = _extract_selected_comments(selected_pair)
        metadata["similarity_score"] = getattr(selected_pair, "similarity_score", 0.0)
        metadata["selection_reason"] = getattr(selected_pair, "selection_reason", "")

    # 検証結果
    validation_result = state.validation_result
    if validation_result:
        metadata["validation_passed"] = getattr(validation_result, "is_valid", False)
        metadata["validation_score"] = getattr(validation_result, "total_score", 0.0)

    # エラーと警告
    if state.errors:
        metadata["errors"] = state.errors
    if state.warnings:
        metadata["warnings"] = state.warnings

    # ユーザー設定
    user_preferences = state.generation_metadata.get("user_preferences", {})
    if user_preferences:
        metadata["style"] = user_preferences.get("style", "casual")
        metadata["length"] = user_preferences.get("length", "medium")

    return metadata


def _extract_selected_comments(selected_pair: Any) -> List[Dict[str, str]]:
    """
    選択されたコメント情報を抽出
    """
    comments = []

    # 天気コメント
    weather_comment = getattr(selected_pair, "weather_comment", None)
    if weather_comment and hasattr(weather_comment, "comment_text"):
        comment_dict = {
            "text": weather_comment.comment_text,
            "type": "weather_comment",
        }
        
        # 気温（有効な値のみ追加）
        temperature = getattr(weather_comment, "temperature", None)
        if temperature is not None:
            comment_dict["temperature"] = temperature
        
        # 天気状況（有効な値のみ追加）
        weather_condition = getattr(weather_comment, "weather_condition", None)
        if weather_condition and weather_condition != "不明":
            comment_dict["weather_condition"] = weather_condition
        
        comments.append(comment_dict)

    # アドバイスコメント
    advice_comment = getattr(selected_pair, "advice_comment", None)
    if advice_comment and hasattr(advice_comment, "comment_text"):
        comment_dict = {
            "text": advice_comment.comment_text,
            "type": "advice",
        }
        
        # 気温（有効な値のみ追加）
        temperature = getattr(advice_comment, "temperature", None)
        if temperature is not None:
            comment_dict["temperature"] = temperature
        
        # 天気状況（有効な値のみ追加）
        weather_condition = getattr(advice_comment, "weather_condition", None)
        if weather_condition and weather_condition != "不明":
            comment_dict["weather_condition"] = weather_condition
        
        comments.append(comment_dict)

    return comments


# デフォルトコメント生成関数は削除（エラーを返すため不要）


def _create_debug_info(state: CommentGenerationState) -> Dict[str, Any]:
    """
    デバッグ情報を作成
    """
    return {
        "state_keys": [attr for attr in dir(state) if not attr.startswith("_")],
        "retry_history": state.generation_metadata.get("evaluation_history", []),
        "node_execution_times": state.generation_metadata.get("node_execution_times", {}),
        "api_call_count": state.generation_metadata.get("api_call_count", 0),
        "cache_hits": state.generation_metadata.get("cache_hits", 0),
        "total_past_comments": len(state.past_comments) if state.past_comments else 0,
        "workflow_version": state.generation_metadata.get("execution_context", {}).get(
            "api_version", "unknown"
        ),
    }


def _cleanup_state(state: CommentGenerationState):
    """
    不要な中間データをクリーンアップ

    メモリ使用量を削減するため、大きな中間データを削除
    """
    # 大きなデータの削除候補
    cleanup_keys = [
        "past_comments",  # 過去コメントの大量データ
        "all_weather_data",  # 詳細な天気データ
        "candidate_pairs",  # 評価前の候補ペア
        "evaluation_details",  # 詳細な評価情報
    ]

    for key in cleanup_keys:
        # メタデータ内の大きなデータをクリーンアップ
        if key in state.generation_metadata:
            value = state.generation_metadata[key]
            if isinstance(value, (list, dict)) and len(str(value)) > 10000:  # 10KB以上
                logger.debug(f"クリーンアップ: {key} を削除")
                del state.generation_metadata[key]


# エクスポート
__all__ = ["output_node"]
