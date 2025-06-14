"""コメントペア選択ノード - LLMを使用して適切なコメントペアを選択"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

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


def select_comment_pair_node(state: CommentGenerationState) -> CommentGenerationState:
    """LLMを使用して適切なコメントペアを選択"""
    logger.info("SelectCommentPairNode: LLMによるコメントペア選択を開始")

    try:
        # 必要なデータの取得
        weather_data = state.weather_data
        past_comments = state.past_comments
        location_name = state.location_name
        target_datetime = state.target_datetime or datetime.now()
        llm_provider = state.llm_provider or "openai"

        if not weather_data:
            raise ValueError("天気データが利用できません")
        if not past_comments:
            raise ValueError("過去コメントが存在しません")

        # コメントをタイプ別に分離
        collection = PastCommentCollection(past_comments)
        weather_comments = collection.filter_by_type(CommentType.WEATHER_COMMENT).comments
        advice_comments = collection.filter_by_type(CommentType.ADVICE).comments

        if not weather_comments or not advice_comments:
            raise ValueError("適切なコメントタイプが見つかりません")

        logger.info(f"天気コメント数: {len(weather_comments)}, アドバイスコメント数: {len(advice_comments)}")

        # LLMマネージャーとバリデーターの初期化
        llm_manager = LLMManager(provider=llm_provider)
        validator = WeatherCommentValidator()
        
        # 天気に適したコメントを事前フィルタリング
        logger.info("天気条件に基づくコメント事前フィルタリングを実行...")
        filtered_weather_comments = validator.get_weather_appropriate_comments(
            weather_comments, weather_data, CommentType.WEATHER_COMMENT, limit=100
        )
        filtered_advice_comments = validator.get_weather_appropriate_comments(
            advice_comments, weather_data, CommentType.ADVICE, limit=100
        )
        
        logger.info(f"フィルタリング結果 - 天気コメント: {len(weather_comments)} -> {len(filtered_weather_comments)}")
        logger.info(f"フィルタリング結果 - アドバイス: {len(advice_comments)} -> {len(filtered_advice_comments)}")

        # 最適なコメントを選択（フィルタリング済みコメントから）
        best_weather = _select_best_comment(
            filtered_weather_comments, weather_data, location_name, target_datetime, 
            llm_manager, CommentType.WEATHER_COMMENT, state
        )
        best_advice = _select_best_comment(
            filtered_advice_comments, weather_data, location_name, target_datetime,
            llm_manager, CommentType.ADVICE, state
        )

        # ペアを作成
        if best_weather and best_advice:
            pair = CommentPair(
                weather_comment=best_weather,
                advice_comment=best_advice,
                similarity_score=1.0,
                selection_reason="LLMによる最適選択",
            )
            
            # 最終バリデーションチェック
            weather_valid, weather_reason = validator.validate_comment(best_weather, weather_data)
            advice_valid, advice_reason = validator.validate_comment(best_advice, weather_data)
            
            if not weather_valid or not advice_valid:
                logger.critical(f"🚨 最終バリデーション失敗:")
                logger.critical(f"   天気コメント: '{best_weather.comment_text}' - {weather_reason}")
                logger.critical(f"   アドバイス: '{best_advice.comment_text}' - {advice_reason}")
                
                # フォールバック: より厳密にフィルタリングして再選択
                logger.critical("🚨 フォールバック選択を実行...")
                
                if not weather_valid:
                    # 天気コメントの再選択
                    strict_weather = validator.filter_comments(filtered_weather_comments[:10], weather_data)
                    if strict_weather:
                        best_weather = strict_weather[0]
                        logger.critical(f"🚨 天気コメント再選択: '{best_weather.comment_text}'")
                
                if not advice_valid:
                    # アドバイスの再選択
                    strict_advice = validator.filter_comments(filtered_advice_comments[:10], weather_data)
                    if strict_advice:
                        best_advice = strict_advice[0]
                        logger.critical(f"🚨 アドバイス再選択: '{best_advice.comment_text}'")
                
                # ペアを更新
                pair = CommentPair(
                    weather_comment=best_weather,
                    advice_comment=best_advice,
                    similarity_score=1.0,
                    selection_reason="バリデーション後再選択",
                )
            
            # 従来の組み合わせチェックも実行（追加チェック）
            if _should_exclude_comment_combination(pair, weather_data):
                logger.critical(f"🚨 組み合わせチェック: 不適切なコメント組み合わせを検出 - 天気: '{best_weather.comment_text}', アドバイス: '{best_advice.comment_text}'")
                
                # 不適切な組み合わせの場合、代替コメントを選択
                logger.critical("🚨 代替コメント選択を実行")
                
                # 雨天に適したコメントを手動選択
                collection = PastCommentCollection(past_comments)
                weather_comments = collection.filter_by_type(CommentType.WEATHER_COMMENT).comments
                advice_comments = collection.filter_by_type(CommentType.ADVICE).comments
                
                # 雨天に適した天気コメントを選択
                rain_weather_comment = None
                for comment in weather_comments:
                    if (any(keyword in comment.comment_text for keyword in ["雨", "荒れ", "心配", "警戒", "注意"]) and
                        not any(forbidden in comment.comment_text for forbidden in ["穏やか", "過ごしやすい", "快適", "爽やか"])):
                        rain_weather_comment = comment
                        break
                
                # 雨天に適したアドバイスコメントを選択
                rain_advice_comment = None
                for comment in advice_comments:
                    if (any(keyword in comment.comment_text for keyword in ["傘", "雨", "濡れ", "注意", "安全", "室内"]) and
                        not any(forbidden in comment.comment_text for forbidden in ["過ごしやすい", "快適", "お出かけ", "散歩"]) and
                        not _should_exclude_advice_comment(comment.comment_text, weather_data)):
                        rain_advice_comment = comment
                        break
                
                if rain_weather_comment and rain_advice_comment:
                    pair = CommentPair(
                        weather_comment=rain_weather_comment,
                        advice_comment=rain_advice_comment,
                        similarity_score=1.0,
                        selection_reason="雨天対応代替選択",
                    )
                    logger.critical(f"🚨 代替選択完了 - 天気: '{rain_weather_comment.comment_text}', アドバイス: '{rain_advice_comment.comment_text}'")
                else:
                    state.errors.append("雨天時に不適切なコメント組み合わせが検出され、代替選択も失敗しました")
                    return state
            
            state.selected_pair = pair
            
            logger.info(f"選択完了 - 天気: {best_weather.comment_text}, アドバイス: {best_advice.comment_text}")
            
            state.update_metadata("selection_metadata", {
                "weather_comments_count": len(weather_comments),
                "advice_comments_count": len(advice_comments),
                "selection_method": "LLM",
                "llm_provider": llm_provider,
                "selected_weather_comment": best_weather.comment_text,
                "selected_advice_comment": best_advice.comment_text,
            })
        else:
            raise ValueError("LLMによるコメントペアの選択に失敗しました")

    except Exception as e:
        logger.error(f"コメントペア選択中にエラー: {e!s}")
        state.add_error(f"SelectCommentPairNode: {e!s}", "select_comment_pair_node")
        raise

    return state


def _select_best_comment(comments: List[PastComment], weather_data: WeatherForecast, location_name: str, target_datetime: datetime, 
                        llm_manager: LLMManager, comment_type: CommentType, state: Optional[CommentGenerationState] = None) -> Optional[PastComment]:
    """LLMを使用して最適なコメントを選択"""
    if not comments:
        return None

    # 悪天候設定を取得
    severe_config = get_severe_weather_config()
    
    # 候補の準備（事前フィルタリング適用）
    candidates = []
    if comment_type == CommentType.WEATHER_COMMENT:
        severe_weather_matched = []  # 悪天候に特化したコメント
        weather_matched = []
        others = []
        
        for i, comment in enumerate(comments):
            # 天気コメントの事前フィルタリング
            if _should_exclude_weather_comment(comment.comment_text, weather_data):
                logger.critical(f"🚨 天気条件不適合のためコメントを除外: '{comment.comment_text}' (天気: {weather_data.weather_description})")
                continue
            else:
                logger.debug(f"✅ コメント通過: '{comment.comment_text}' (天気: {weather_data.weather_description})")
                
            candidate = _create_candidate_dict(len(severe_weather_matched) + len(weather_matched) + len(others), comment, original_index=i)
            
            # 悪天候時の特別な優先順位付け
            if severe_config.is_severe_weather(weather_data.weather_condition):
                # 悪天候に適したコメントかチェック
                if _is_severe_weather_appropriate(comment.comment_text, weather_data):
                    severe_weather_matched.append(candidate)
                elif _is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
            else:
                # 通常の天気マッチング
                if _is_weather_matched(comment.weather_condition, weather_data.weather_description):
                    weather_matched.append(candidate)
                else:
                    others.append(candidate)
        
        # 悪天候時の強制除外処理（二重チェック）
        is_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        
        # 未来の悪天候を事前チェック
        has_future_severe = False
        if state and hasattr(state, 'location_name') and weather_data and weather_data.datetime:
            try:
                from src.data.forecast_cache import ForecastCache
                from datetime import timedelta
                cache = ForecastCache()
                for hours in [3, 6, 9, 12, 15, 18, 21, 24]:  # 24時間先まで拡張
                    future_time = weather_data.datetime + timedelta(hours=hours)
                    forecast = cache.get_forecast_at_time(state.location_name, future_time)
                    if forecast and any(pattern in forecast.weather_description for pattern in ['大雨・嵐', '嵐', '暴風', '台風', '雷', '豪雨']):
                        has_future_severe = True
                        break
            except Exception as e:
                logger.debug(f"未来悪天候チェックエラー: {e}")
        
        logger.critical(f"🚨 除外処理チェック: is_severe={is_severe}, has_future_severe={has_future_severe}")
        logger.critical(f"🚨 天気条件: {weather_data.weather_condition}, 説明: {weather_data.weather_description}")
        
        if is_severe or has_future_severe:
            # 軽微な表現を強制的に除外
            # 大雨・嵐予報時は軽微な表現を全て除外
            forbidden_phrases = [
                "ニワカ雨が心配", "にわか雨が心配", "スッキリしない空", "変わりやすい空", 
                "蒸し暑い", "厳しい暑さ", "過ごしやすい体感", "過ごしやすい", "快適",
                "にわか雨", "ニワカ雨",  # 大雨・嵐時には軽すぎる
                "体感", "心地", "爽やか", "穏やか", "のどか", "静か",  # 追加の肯定的表現
                "暑さ", "寒さ"  # 天候ではなく気温のみに焦点を当てた表現
            ]
            
            # 大雨・嵐時には強い警戒コメントのみ許可
            if has_future_severe:
                required_phrases = ["強雨", "雷雨", "警戒", "注意", "危険", "安全", "控えめ", "室内"]
                # 強い警戒表現を含むコメントのみ残す
                severe_weather_matched = [c for c in severe_weather_matched if any(phrase in c['text'] for phrase in required_phrases)]
                weather_matched = [c for c in weather_matched if any(phrase in c['text'] for phrase in required_phrases)]
                others = [c for c in others if any(phrase in c['text'] for phrase in required_phrases)]
                logger.critical(f"🚨 大雨・嵐時強制フィルター: 強い警戒表現のみ許可")
            
            # 除外前の件数をログ
            logger.critical(f"🚨 除外前: severe={len(severe_weather_matched)}, weather={len(weather_matched)}, others={len(others)}")
            
            # 実際に除外されるコメントをログ出力
            for category, candidates in [("severe", severe_weather_matched), ("weather", weather_matched), ("others", others)]:
                for c in candidates:
                    for phrase in forbidden_phrases:
                        if phrase in c['text']:
                            logger.critical(f"🚨 除外対象発見: [{category}] '{c['text']}' contains '{phrase}'")
            
            severe_weather_matched = [c for c in severe_weather_matched if not any(phrase in c['text'] for phrase in forbidden_phrases)]
            weather_matched = [c for c in weather_matched if not any(phrase in c['text'] for phrase in forbidden_phrases)]
            others = [c for c in others if not any(phrase in c['text'] for phrase in forbidden_phrases)]
            
            # 除外後の件数をログ
            logger.critical(f"🚨 除外後: severe={len(severe_weather_matched)}, weather={len(weather_matched)}, others={len(others)}")
            logger.critical(f"🚨 悪天候時強制除外処理実行: {forbidden_phrases}")
        else:
            logger.info("除外処理スキップ: 悪天候条件に該当せず")
        
        # 悪天候時は悪天候用コメントを最優先、次に天気一致、最後にその他
        candidates = severe_weather_matched[:15] + weather_matched[:10] + others[:5]
        logger.info(f"天気コメント候補: 全{len(comments)}件中、悪天候専用{len(severe_weather_matched)}件、天気一致{len(weather_matched)}件を優先")
        
        # 除外処理後に候補がゼロになった場合、悪天候に適したコメントから再選択
        if not candidates and (is_severe or has_future_severe):
            logger.warning("すべての候補が除外されました。悪天候用の基本コメントから選択します。")
            # 悪天候に適した基本コメントを手動で追加
            for i, comment in enumerate(comments):
                if any(keyword in comment.comment_text for keyword in ["雨", "荒れ", "崩れ", "心配", "警戒", "注意"]):
                    candidate = _create_candidate_dict(len(candidates), comment, original_index=i)
                    candidates.append(candidate)
                    if len(candidates) >= 5:
                        break
    else:
        # アドバイスコメントの事前フィルタリング
        severe_advice_matched = []  # 悪天候に適したアドバイス
        normal_advice = []
        
        # アドバイス用の悪天候チェック
        is_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        
        # 未来の悪天候を事前チェック（アドバイス用）
        has_future_severe = False
        if state and hasattr(state, 'location_name') and weather_data and weather_data.datetime:
            try:
                from src.data.forecast_cache import ForecastCache
                from datetime import timedelta
                cache = ForecastCache()
                for hours in [3, 6, 9, 12]:
                    future_time = weather_data.datetime + timedelta(hours=hours)
                    forecast = cache.get_forecast_at_time(state.location_name, future_time)
                    if forecast and any(pattern in forecast.weather_description for pattern in ['大雨・嵐', '嵐', '暴風', '台風', '雷', '豪雨']):
                        has_future_severe = True
                        break
            except Exception as e:
                logger.debug(f"アドバイス用未来悪天候チェックエラー: {e}")
        
        for i, comment in enumerate(comments):
            # アドバイスコメントの事前フィルタリング
            if _should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.info(f"天気・気温条件不適合のためコメントを除外: {comment.comment_text}")
                continue
            
            candidate = _create_candidate_dict(len(severe_advice_matched) + len(normal_advice), comment, original_index=i)
            
            # 悪天候時の特別な優先順位付け
            if severe_config.is_severe_weather(weather_data.weather_condition):
                if _is_severe_weather_advice_appropriate(comment.comment_text, weather_data):
                    severe_advice_matched.append(candidate)
                else:
                    normal_advice.append(candidate)
            else:
                normal_advice.append(candidate)
        
        # アドバイスコメントでも悪天候時の強制除外処理
        if is_severe or has_future_severe:
            # 軽微な表現を強制的に除外
            forbidden_phrases = [
                "ニワカ雨が心配", "にわか雨が心配", "スッキリしない空", "変わりやすい空", 
                "蒸し暑い", "厳しい暑さ", "過ごしやすい体感", "過ごしやすい", "快適",
                "体感", "心地", "爽やか", "穏やか", "のどか", "静か"  # アドバイスでも同様に除外
            ]
            
            # 除外前の件数をログ
            logger.critical(f"🚨 アドバイス除外前: severe={len(severe_advice_matched)}, normal={len(normal_advice)}")
            
            # 実際に除外されるコメントをログ出力
            for category, candidates in [("advice_severe", severe_advice_matched), ("advice_normal", normal_advice)]:
                for c in candidates:
                    for phrase in forbidden_phrases:
                        if phrase in c['text']:
                            logger.critical(f"🚨 アドバイス除外対象発見: [{category}] '{c['text']}' contains '{phrase}'")
            
            severe_advice_matched = [c for c in severe_advice_matched if not any(phrase in c['text'] for phrase in forbidden_phrases)]
            normal_advice = [c for c in normal_advice if not any(phrase in c['text'] for phrase in forbidden_phrases)]
            
            # 除外後の件数をログ
            logger.critical(f"🚨 アドバイス除外後: severe={len(severe_advice_matched)}, normal={len(normal_advice)}")
            logger.critical(f"🚨 アドバイス悪天候時強制除外処理実行: {forbidden_phrases}")
        
        # 悪天候時は安全重視のアドバイスを優先
        candidates = severe_advice_matched[:15] + normal_advice[:15]
        logger.info(f"アドバイス候補: 悪天候用{len(severe_advice_matched)}件を優先")
        
        # 除外処理後に候補がゼロになった場合、安全対策系のアドバイスから再選択
        if not candidates and (is_severe or has_future_severe):
            logger.warning("すべてのアドバイス候補が除外されました。安全対策系の基本アドバイスから選択します。")
            # 安全対策に適した基本アドバイスを手動で追加
            for i, comment in enumerate(comments):  # 全コメントから選択
                # 禁止フレーズを含まないことを確認
                if not any(phrase in comment.comment_text for phrase in forbidden_phrases):
                    # 温度に不適切でないことを確認
                    if not _should_exclude_advice_comment(comment.comment_text, weather_data):
                        # 雨天・悪天候に適したキーワードを含むコメントを選択
                        if any(keyword in comment.comment_text for keyword in ["傘", "雨", "室内", "注意", "安全", "準備", "対策", "心配", "警戒"]):
                            candidate = _create_candidate_dict(len(candidates), comment, original_index=i)
                            candidates.append(candidate)
                            if len(candidates) >= 5:
                                break

    # プロンプト生成（stateを渡す）
    prompt = _generate_prompt(candidates, weather_data, location_name, target_datetime, comment_type, state)

    try:
        response = llm_manager.generate(prompt)
        match = re.search(r"\d+", response)
        selected_index = int(match.group()) if match else 0

        logger.debug(f"LLM応答: {response}, 選択インデックス: {selected_index}, 候補数: {len(candidates)}, コメント数: {len(comments)}")
        
        if 0 <= selected_index < len(candidates):
            selected_candidate = candidates[selected_index]
            original_index = selected_candidate.get('original_index', selected_index)
            selected_comment = comments[original_index] if 0 <= original_index < len(comments) else None
            
            if selected_comment:
                logger.critical(f"🚨 最終選択コメント: '{selected_comment.comment_text}'")
                
                # 禁止表現チェック（強化版）
                forbidden_check = [
                    "ニワカ雨が心配", "にわか雨が心配", "スッキリしない空", "変わりやすい空", 
                    "蒸し暑い", "厳しい暑さ", "過ごしやすい体感", "過ごしやすい", "快適",
                    "にわか雨", "ニワカ雨", "体感", "心地", "爽やか", "穏やか",
                    # 雨天時に矛盾する表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", "梅雨明け"
                ]
                for phrase in forbidden_check:
                    if phrase in selected_comment.comment_text:
                        logger.critical(f"🚨 警告: 禁止表現'{phrase}'が最終選択されました！ コメント: '{selected_comment.comment_text}'")
                
                logger.info(f"LLMが{comment_type.value}を選択: candidates[{selected_index}] -> comments[{original_index}]")
                return selected_comment
            else:
                logger.error(f"original_indexが範囲外: {original_index} (comments数: {len(comments)})")
        else:
            logger.warning(f"無効なインデックス: {selected_index} (候補数: {len(candidates)})")
        
        # フォールバック処理を改善: 候補リストの最初の要素を選択（フィルタリング済み）
        if candidates:
            fallback_candidate = candidates[0]
            fallback_original_index = fallback_candidate.get('original_index', 0)
            fallback_comment = comments[fallback_original_index] if 0 <= fallback_original_index < len(comments) else None
            
            if fallback_comment:
                logger.critical(f"🚨 フォールバック選択: candidates[0] -> comments[{fallback_original_index}]: '{fallback_comment.comment_text}'")
                return fallback_comment
        
        # 最終的なフォールバック: 適切なコメントを手動選択
        logger.critical("🚨 緊急フォールバック: 手動で適切なコメントを選択")
        severe_config = get_severe_weather_config()
        is_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        
        # 悪天候時は警戒・注意系のコメントを優先
        forbidden_check = [
            "ニワカ雨が心配", "にわか雨が心配", "スッキリしない空", "変わりやすい空", 
            "蒸し暑い", "厳しい暑さ", "過ごしやすい体感", "過ごしやすい", "快適",
            "にわか雨", "ニワカ雨", "体感", "心地", "爽やか", "穏やか",
            # 雨天時に矛盾する表現を追加
            "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", "梅雨明け"
        ]
        
        if is_severe or any(rain_word in weather_data.weather_description.lower() for rain_word in ["雨", "大雨", "豪雨"]):
            for comment in comments:
                # 雨天に適したキーワードを含み、禁止表現を含まないコメントを選択
                if (any(keyword in comment.comment_text for keyword in ["雨", "荒れ", "崩れ", "心配", "警戒", "注意", "安全"]) and
                    not any(forbidden in comment.comment_text for forbidden in forbidden_check)):
                    logger.critical(f"🚨 緊急選択（悪天候対応）: '{comment.comment_text}'")
                    return comment
        
        # それでも見つからない場合は適切なコメントを検索
        for comment in comments:
            if not _should_exclude_advice_comment(comment.comment_text, weather_data):
                logger.critical(f"🚨 最終フォールバック選択: '{comment.comment_text}' (温度・天気条件チェック済み)")
                return comment
        
        # それでも見つからない場合は最初のコメント
        logger.critical(f"🚨 緊急フォールバック: 最初のコメントを選択: '{comments[0].comment_text}'")
        return comments[0]

    except Exception as e:
        raise ValueError(f"{comment_type.value}選択失敗: {e!s}")


def _create_candidate_dict(index: int, comment: PastComment, original_index: Optional[int] = None) -> Dict[str, Any]:
    """候補辞書を作成"""
    return {
        "index": index,
        "original_index": original_index if original_index is not None else index,
        "text": comment.comment_text,
        "season": comment.raw_data.get("season", "不明"),
    }


def _should_exclude_comment_combination(pair: CommentPair, weather_data: WeatherForecast) -> bool:
    """コメントペアの組み合わせが不適切かどうか判定"""
    weather_text = pair.weather_comment.comment_text
    advice_text = pair.advice_comment.comment_text
    current_weather = weather_data.weather_description.lower()
    
    # 雨天時の特別チェック（強化版）
    if any(rain_word in current_weather for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
        
        # 禁止される天気コメント + アドバイス組み合わせ
        inappropriate_weather = ["穏やかな空", "雲の多い空", "過ごしやすい", "快適", "爽やか", "中休み", "晴れ間", "梅雨の中休み"]
        inappropriate_advice = ["過ごしやすい体感", "快適", "心地良い", "爽やか", "穏やか"]
        
        # 雨天時に不適切な天気コメントをチェック
        if any(keyword in weather_text for keyword in inappropriate_weather):
            logger.critical(f"🚨 雨天時不適切天気コメント: '{weather_text}' (天気: {weather_data.weather_description})")
            return True
        
        # 雨天時に不適切なアドバイスをチェック
        if any(keyword in advice_text for keyword in inappropriate_advice):
            logger.critical(f"🚨 雨天時不適切アドバイス: '{advice_text}' (天気: {weather_data.weather_description})")
            return True
        
        # 特定の組み合わせも除外
        if "雲の多い空" in weather_text and "過ごしやすい体感" in advice_text:
            logger.critical(f"🚨 特別除外: 雨天時の最悪組み合わせ - '{weather_text}' + '{advice_text}'")
            return True
        
        # その他の雨天時不適切な組み合わせ
        comfort_keywords = ["過ごしやすい", "快適", "心地良い", "爽やか", "穏やか"]
        if any(keyword in advice_text for keyword in comfort_keywords):
            if any(unsuitable in weather_text for unsuitable in ["雲の多い空", "どんより", "穏やか"]):
                logger.critical(f"🚨 雨天時不適切組み合わせ: '{weather_text}' + '{advice_text}'")
                return True
    
    # 悪天候時の一般的なチェック
    severe_weather = ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]
    if any(severe in current_weather for severe in severe_weather):
        # 穏やかさや快適さを表現する組み合わせを全て除外
        comfort_weather = ["穏やか", "過ごしやすい", "快適", "爽やか", "心地良い"]
        comfort_advice = ["過ごしやすい", "快適", "心地良い", "爽やか", "穏やか"]
        
        if (any(keyword in weather_text for keyword in comfort_weather) or 
            any(keyword in advice_text for keyword in comfort_advice)):
            logger.critical(f"🚨 悪天候時不適切組み合わせ: '{weather_text}' + '{advice_text}' (天気: {weather_data.weather_description})")
            return True
    
    return False


def _should_exclude_weather_comment(comment_text: str, weather_data: WeatherForecast) -> bool:
    """天気コメントを除外すべきかどうか判定"""
    current_weather = weather_data.weather_description.lower()
    comment_lower = comment_text.lower()
    precipitation = weather_data.precipitation
    
    # 降水量レベルを取得
    precipitation_severity = weather_data.get_precipitation_severity()
    
    # 激しい悪天候時の不適切なコメント（降水量も考慮）
    severe_weather_keywords = ["大雨", "豪雨", "嵐", "暴風", "台風"]
    is_severe_weather = any(severe_word in current_weather for severe_word in severe_weather_keywords)
    
    # 雷は降水量によって判定を変える
    thunder_in_weather = "雷" in current_weather
    is_severe_thunder = thunder_in_weather and precipitation >= 5.0
    
    if is_severe_weather or is_severe_thunder:
        # 穏やかさや過ごしやすさを表現するコメントを除外
        if any(calm_word in comment_lower for calm_word in ["穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか", "静か", "体感"]):
            return True
        # 晴天関連のコメントを除外
        if any(sunny_word in comment_lower for sunny_word in ["青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい"]):
            return True
    
    # 軽微な雷（降水量5mm未満）の場合は、軽い警戒コメントは許可
    elif thunder_in_weather and precipitation < 5.0:
        # 軽微な雷の場合、強い警戒表現は避ける
        strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
        if any(warning in comment_lower for warning in strong_warning_words):
            logger.info(f"軽微な雷（降水量{precipitation}mm）のため強い警戒コメントを除外: '{comment_text}'")
            return True
    
    # 雨天時の不適切なコメント（降水量を考慮した強化版）
    if any(rain_word in current_weather for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
        # 晴天関連のコメントを除外
        if any(sunny_word in comment_lower for sunny_word in ["青空", "晴れ", "快晴", "日差し", "太陽", "陽射し"]):
            return True
        # 外出推奨系コメントを除外
        if any(outdoor_word in comment_lower for outdoor_word in ["お出かけ", "外出", "散歩", "ピクニック", "日和"]):
            return True
        
        # 降水量に応じた除外基準
        if precipitation_severity in ["heavy", "very_heavy"]:  # 大雨・激しい雨
            # 強い雨の場合は穏やかなコメントを除外
            if any(calm_word in comment_lower for calm_word in ["穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "体感"]):
                return True
        elif precipitation_severity == "moderate":  # 中程度の雨
            # 中程度の雨では快適系のみ除外
            if any(comfort_word in comment_lower for comfort_word in ["過ごしやすい", "快適", "心地良い"]):
                return True
        elif precipitation_severity == "light":  # 軽い雨（1-2mm）
            # 軽い雨では強い警戒表現を除外
            strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
            if any(warning in comment_lower for warning in strong_warning_words):
                logger.info(f"軽い雨（降水量{precipitation}mm）のため強い警戒コメントを除外: '{comment_text}'")
                return True
        
        # 「雲の多い空」と「過ごしやすい」を含むコメントは雨天時に除外
        if "雲の多い空" in comment_text and "過ごしやすい" in comment_text:
            logger.critical(f"🚨 特別除外: '雲の多い空　過ごしやすい体感' は雨天時に不適切")
            return True
        
        # 雨天時に「中休み」「晴れ間」などの矛盾表現を除外
        contradictory_phrases = ["中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", "梅雨明け", "からっと", "さっぱり"]
        for phrase in contradictory_phrases:
            if phrase in comment_text:
                logger.critical(f"🚨 雨天時矛盾表現除外: '{phrase}' を含むコメント '{comment_text}' は雨天時に不適切")
                return True
        # 「〜やすい」で終わる肯定的表現も中程度以上の雨で除外
        if precipitation_severity in ["moderate", "heavy", "very_heavy"]:
            if "やすい" in comment_text and not any(neg in comment_text for neg in ["降りやすい", "崩れやすい", "変わりやすい"]):
                return True
    
    # 晴天時の不適切なコメント  
    if any(sunny_word in current_weather for sunny_word in ["晴れ", "快晴"]):
        if any(rain_word in comment_lower for rain_word in ["雨", "じめじめ", "湿った", "どんより"]):
            return True
    
    # 曇天時の不適切なコメント（強化版）
    if "くもり" in current_weather or "曇" in current_weather:
        if any(sunny_word in comment_lower for sunny_word in ["青空", "快晴", "眩しい"]):
            return True
        # 曇天時も快適系を除外（特に雨が降る可能性がある場合）
        if "雨" in current_weather:
            if any(calm_word in comment_lower for calm_word in ["過ごしやすい", "快適", "心地良い", "体感"]):
                return True
    
    # 気温による不適切なコメント
    if weather_data.temperature < 10 and any(hot_word in comment_lower for hot_word in ["暑い", "猛暑", "酷暑"]):
        return True
    if weather_data.temperature > 30 and any(cold_word in comment_lower for cold_word in ["寒い", "冷える", "肌寒い"]):
        return True
    
    return False


def _should_exclude_advice_comment(comment_text: str, weather_data: WeatherForecast) -> bool:
    """アドバイスコメントを除外すべきかどうか判定"""
    current_weather = weather_data.weather_description.lower()
    comment_lower = comment_text.lower()
    precipitation = weather_data.precipitation
    
    # 降水量レベルを取得
    precipitation_severity = weather_data.get_precipitation_severity()
    
    # 設定から温度閾値を取得
    config = get_comment_config()
    heat_threshold = config.heat_warning_threshold
    cold_threshold = config.cold_warning_threshold
    
    # 激しい悪天候時は適切なアドバイスを優先（降水量も考慮）
    severe_weather_keywords = ["大雨", "豪雨", "嵐", "暴風", "台風"]
    is_severe_weather = any(severe_word in current_weather for severe_word in severe_weather_keywords)
    
    # 雷は降水量によって判定を変える
    thunder_in_weather = "雷" in current_weather
    is_severe_thunder = thunder_in_weather and precipitation >= 5.0
    
    if is_severe_weather or is_severe_thunder:
        # 悪天候時の不適切なアドバイスを除外
        if any(good_weather_advice in comment_lower for good_weather_advice in ["散歩", "外出", "お出かけ", "ピクニック", "日光浴"]):
            return True
        # 晴天向けアドバイスを除外
        if any(sunny_advice in comment_lower for sunny_advice in ["日焼け止め", "帽子", "サングラス", "日傘"]):
            return True
    
    # 軽微な雷（降水量5mm未満）の場合は、軽い注意喚起のみ
    elif thunder_in_weather and precipitation < 5.0:
        # 軽微な雷の場合、強い警戒アドバイスは避ける
        strong_warning_advice = ["避難", "危険", "中止", "延期", "控える"]
        if any(warning in comment_lower for warning in strong_warning_advice):
            logger.info(f"軽微な雷（降水量{precipitation}mm）のため強い警戒アドバイスを除外: '{comment_text}'")
            return True
    
    # 気温による除外
    if weather_data.temperature < heat_threshold and "熱中症" in comment_text:
        logger.critical(f"🚨 温度による熱中症コメント除外: '{comment_text}' (気温: {weather_data.temperature}°C < {heat_threshold}°C)")
        return True
    if weather_data.temperature >= cold_threshold and any(word in comment_text for word in ["防寒", "暖かく", "寒さ"]):
        return True
    
    # 雨天時の不適切なアドバイス（降水量を考慮）
    if any(rain_word in current_weather for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
        # 晴天向けアドバイスを除外
        if any(sunny_advice in comment_lower for sunny_advice in ["日焼け止め", "帽子", "サングラス", "日傘"]):
            return True
        
        # 降水量に応じたアドバイス除外基準
        if precipitation_severity in ["heavy", "very_heavy"]:  # 大雨・激しい雨
            # 強い雨の場合は外出推奨系を全て除外
            if any(outdoor_advice in comment_lower for outdoor_advice in ["お出かけ", "外出", "散歩", "ピクニック", "日和"]):
                return True
        elif precipitation_severity in ["moderate"]:  # 中程度の雨
            # 中程度の雨では一部の外出推奨を除外
            if any(strong_outdoor in comment_lower for strong_outdoor in ["散歩", "ピクニック", "日和"]):
                return True
        elif precipitation_severity == "light":  # 軽い雨（1-2mm）
            # 軽い雨では強い警戒アドバイスを除外
            strong_warning_advice = ["外出控える", "中止", "延期", "危険", "避難"]
            if any(warning in comment_lower for warning in strong_warning_advice):
                logger.info(f"軽い雨（降水量{precipitation}mm）のため強い警戒アドバイスを除外: '{comment_text}'")
                return True
    
    # 晴天時の不適切なアドバイス
    if any(sunny_word in current_weather for sunny_word in ["晴れ", "快晴"]):
        if any(rain_advice in comment_lower for rain_advice in ["傘", "レインコート", "濡れ"]):
            return True
    
    # 低湿度時の不適切なアドバイス
    if weather_data.humidity < 30 and any(humid_advice in comment_lower for humid_advice in ["除湿", "湿気対策"]):
        return True
    
    # 高湿度時の不適切なアドバイス  
    if weather_data.humidity > 80 and any(dry_advice in comment_lower for dry_advice in ["乾燥対策", "保湿"]):
        return True
    
    return False


def _is_weather_matched(comment_weather: str, current_weather: str) -> bool:
    """天気条件が一致するか判定"""
    if not comment_weather or not current_weather:
        return False
    return current_weather in comment_weather or comment_weather in current_weather


def _is_severe_weather_appropriate(comment_text: str, weather_data: WeatherForecast) -> bool:
    """コメントが悪天候に適しているか判定"""
    comment_lower = comment_text.lower()
    severe_config = get_severe_weather_config()
    
    # 悪天候を示唆するキーワードがあるかチェック
    severe_keywords = [
        "荒れ", "激し", "警戒", "注意", "不安定", "変わりやすい", 
        "スッキリしない", "崩れ", "悪化", "心配", "必須", "警報",
        "視界", "慎重", "安全", "控えめ", "様子", "傘", "雨",
        "ニワカ", "どんより", "じめじめ", "湿った"
    ]
    
    # 悪天候キーワードが含まれているか
    has_severe_keyword = any(keyword in comment_lower for keyword in severe_keywords)
    
    # 除外キーワードが含まれていないか
    has_exclude_keyword = any(keyword in comment_lower for keyword in severe_config.exclude_keywords_severe)
    
    return has_severe_keyword and not has_exclude_keyword


def _is_severe_weather_advice_appropriate(comment_text: str, weather_data: WeatherForecast) -> bool:
    """アドバイスが悪天候に適しているか判定"""
    comment_lower = comment_text.lower()
    severe_config = get_severe_weather_config()
    
    # 悪天候時に推奨されるアドバイスキーワード
    severe_advice_keywords = [
        "室内", "屋内", "安全", "慎重", "警戒", "注意",
        "早め", "備え", "確認", "中止", "延期", "控え",
        "無理", "避け", "気をつけ", "余裕", "ゆっくり",
        "傘", "雨具", "濡れ", "心配", "必須", "お守り"
    ]
    
    # 悪天候アドバイスキーワードが含まれているか
    has_severe_keyword = any(keyword in comment_lower for keyword in severe_advice_keywords)
    
    # 除外キーワードが含まれていないか（お出かけ系など）
    outdoor_keywords = ["散歩", "外出", "お出かけ", "ピクニック", "外遊び", "日光浴", "日焼け"]
    has_outdoor_keyword = any(keyword in comment_lower for keyword in outdoor_keywords)
    
    return has_severe_keyword and not has_outdoor_keyword


def _generate_prompt(candidates: List[Dict[str, Any]], weather_data: WeatherForecast, location_name: str, target_datetime: datetime, comment_type: CommentType, state: Optional[CommentGenerationState] = None) -> str:
    """選択用プロンプトを生成"""
    
    # 時系列データの取得と分析（直接ForecastCacheから取得）
    timeline_info = ""
    severe_future_warning = ""
    
    location_name_param = state.location_name if state else None
    if location_name_param and weather_data and weather_data.datetime:
        try:
            cache = ForecastCache()
            future_forecasts = []
            
            # 未来の予報を直接取得（3, 6, 9, 12, 15, 18, 21, 24時間後）
            for hours in [3, 6, 9, 12, 15, 18, 21, 24]:
                future_time = weather_data.datetime + timedelta(hours=hours)
                try:
                    forecast = cache.get_forecast_at_time(location_name_param, future_time)
                    if forecast:
                        future_forecasts.append({
                            'label': f'+{hours}h',
                            'weather': forecast.weather_description,
                            'temperature': forecast.temperature,
                            'precipitation': forecast.precipitation
                        })
                except Exception as e:
                    logger.debug(f"未来予報取得エラー (+{hours}h): {e}")
            
            # 未来の悪天候を検出（強化版）
            if future_forecasts:
                severe_future = []
                for forecast in future_forecasts:
                    weather_desc = forecast.get('weather', '')
                    # より包括的な悪天候検出パターン
                    severe_patterns = [
                        '大雨・嵐', '嵐', '暴風', '台風', '雷', '豪雨', '大雨',
                        '暴風雨', '激しい雨', '強い雨', '大荒れ', '荒天',
                        '雷雨', '激雷', '雷鳴'
                    ]
                    
                    # パターンマッチングを改善
                    detected_conditions = []
                    for pattern in severe_patterns:
                        if pattern in weather_desc:
                            detected_conditions.append(pattern)
                    
                    if detected_conditions:
                        severity_level = "⚠️ 警戒" if any(x in detected_conditions for x in ['大雨・嵐', '嵐', '台風', '暴風']) else "⚠️ 注意"
                        severe_future.append(f"{forecast['label']}: {weather_desc} ({severity_level})")
                
                if severe_future:
                    # より強力な警告メッセージ
                    severe_future_warning = f"""
🚨【緊急警告】今後悪天候が予想されています:
{chr(10).join(f'- {warning}' for warning in severe_future)}

⚠️ 必須条件: 以下を満たすコメントを最優先選択:
  - 警戒・注意を強く促す表現
  - 「蒸し暑い」「スッキリしない」「ニワカ雨が心配」等の軽微な表現は絶対に避ける
  - 安全対策や備えを示唆する内容
  - 悪天候の影響を具体的に表現する内容
  - 今後の天候悪化を明確に示す表現を最優先"""
                
                timeline_info = f"""
                
【時系列予報情報】
- 今後の変化: {len(future_forecasts)}時点の予報あり
- 悪天候検出: {len(severe_future)}件の警告"""
        
        except Exception as e:
            logger.warning(f"時系列データ取得エラー: {e}")
    
    # WeatherTrendの取得（既存）
    weather_trend_info = ""
    if state and hasattr(state, 'generation_metadata'):
        weather_trend = state.generation_metadata.get('weather_trend')
        if weather_trend:
                weather_trend_info = f"""
                
今後12時間の気象変化:
- 気温変化: {weather_trend.temperature_change:+.1f}°C ({weather_trend.min_temperature:.1f}°C〜{weather_trend.max_temperature:.1f}°C)
- 天気変化: {weather_trend.get_summary()}
- 傾向: 天気は{weather_trend.weather_trend.value}、気温は{weather_trend.temperature_trend.value}"""
    
    base = f"""現在の天気条件に最も適した{comment_type.value}を選んでください。

現在の条件:
- 地点: {location_name}
- 天気: {weather_data.weather_description}
- 気温: {weather_data.temperature}°C
- 湿度: {weather_data.humidity}%
- 風速: {weather_data.wind_speed}m/s
- 降水量: {weather_data.precipitation}mm
- 日時: {target_datetime.strftime("%Y年%m月%d日 %H時")}{timeline_info}{weather_trend_info}{severe_future_warning}

候補:
{json.dumps(candidates, ensure_ascii=False, indent=2)}

"""

    if comment_type == CommentType.WEATHER_COMMENT:
        # 悪天候時の特別な指示
        severe_config = get_severe_weather_config()
        severe_instruction = ""
        
        # 現在または未来の悪天候チェック
        current_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        future_severe = bool(severe_future_warning)
        
        if current_severe or future_severe:
            current_desc = f"現在は{weather_data.weather_description}" if current_severe else "現在は軽微な天候"
            future_desc = "、さらに今後悪天候が予想されています" if future_severe else ""
            
            # 悪天候の重要度に基づいて指示を強化
            severity_level = "🚨 最高警戒" if future_severe else "⚠️ 警戒"
            
            severe_instruction = f"""
🚨【{severity_level}】{current_desc}{future_desc}。

❌ 絶対に避けるコメント（これらを選択した場合は即座に不適切として却下）:
  - 「スッキリしない空」「蒸し暑い」「ニワカ雨が心配」等の軽微な表現
  - 「変わりやすい空」「にわか雨が心配」等の軽視表現
  - 快適さや穏やかさを示唆する表現
  - 天候の深刻さを軽視する表現
  - 現在進行中または予想される悪天候を過小評価する表現

✅ 必須選択基準:
1. 【最優先】悪天候に対する警戒・注意を強く促す表現
2. 安全対策や備えの必要性を示唆する内容
3. 天候の厳しさや危険性を具体的に表現
4. 外出時の注意喚起を含む表現
5. 気象状況の変化への備えを促す内容

⚠️ 特に今後悪天候が予想される場合は、現在が軽微でも将来への警戒を最優先してください！
"""
        
        # 気象変化を考慮した追加基準
        trend_criteria = ""
        if state and hasattr(state, 'generation_metadata'):
            weather_trend = state.generation_metadata.get('weather_trend')
            if weather_trend:
                if weather_trend.has_weather_change:
                    trend_criteria = "\n4. 気象変化の考慮：今後天気が変わるため、変化を示唆する表現を優先"
                if abs(weather_trend.temperature_change) >= 5:
                    trend_criteria += f"\n5. 気温変化の考慮：{weather_trend.temperature_change:+.1f}°Cの変化があるため、それを反映した表現を優先"
        
        # 特殊気象条件の優先基準（天気コメント用）- 強化版
        special_criteria = ""
        if weather_data.weather_condition.is_special_condition:
            special_criteria = f"\n\n🔥【最高優先】{weather_data.weather_condition.value}に関連するコメントを絶対選択："
            if weather_data.weather_condition.value == "thunder":
                special_criteria += "\n   ⚡ 「雷」「雷雨」「ゴロゴロ」「急な雷雨」「雷に注意」「安全確保」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "fog":
                special_criteria += "\n   🌫️ 「霧」「かすむ」「視界不良」「霧の危険」「運転注意」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "storm":
                special_criteria += "\n   🌪️ 「嵐」「暴風」「荒れる」「嵐に警戒」「外出危険」「強風注意」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "severe_storm":  # 大雨・嵐対応
                special_criteria += "\n   🌊⚡ 「大雨・嵐」「激しい雨風」「警戒が必要」「安全第一」「外出控えて」などの表現を含むコメント"
            elif weather_data.weather_condition.value == "extreme_heat":
                special_criteria += "\n   🔥 「猛暑」「酷暑」「熱中症」「暑さ対策」「命に関わる暑さ」などの表現を含むコメント"
            
            special_criteria += "\n\n❗ 軽微な表現（「スッキリしない」「蒸し暑い」等）は特殊気象条件では絶対に選択しないでください"
        
        # 悪天候時の特別な基準を追加
        severe_weather_criteria = ""
        if any(severe in weather_data.weather_description.lower() for severe in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
            severe_weather_criteria = f"""

【重要】悪天候時の選択基準:
⚠️ 現在は「{weather_data.weather_description}」という激しい天候です
- 「穏やか」「過ごしやすい」「快適」などの表現は絶対に避ける
- 「荒れる」「注意」「気をつけて」などの警戒を促す表現を優先
- 悪天候の状況を適切に表現するコメントを選択"""

        # 未来の悪天候による基準強化
        future_criteria = ""
        if future_severe:
            future_criteria = "\n6. 【最重要】今後の悪天候を考慮し、より強い警戒コメントを選択（「大荒れ」「激しい」「警戒」等）"
        
        base += f"""{severe_instruction}{special_criteria}{severe_weather_criteria}

選択基準:
1. 【最優先】悪天候時は危険性や注意を促すコメント
2. 【重要】天気条件の一致（雨なら「本格的な雨に注意」等、嵐なら「荒れる」等）
3. 気温表現の適合性（{weather_data.temperature}°Cに適した表現）
4. 【絶対禁止】以下のコメントは選択禁止:
   - 「ニワカ雨が心配」「にわか雨が心配」「スッキリしない空」「変わりやすい空」
   - 悪天候時+「穏やか」系、雨天+「晴れ」系、気温不一致{trend_criteria}{future_criteria}

現在は{weather_data.weather_description}・{weather_data.temperature}°Cです。安全で適切な表現を選んでください。"""
    else:
        # 悪天候時の特別な指示（アドバイス用）
        severe_config = get_severe_weather_config()
        severe_instruction = ""
        
        # 現在または未来の悪天候チェック（アドバイス用）
        current_severe = severe_config.is_severe_weather(weather_data.weather_condition)
        future_severe = bool(severe_future_warning)
        
        if current_severe or future_severe:
            current_desc = f"現在は{weather_data.weather_description}" if current_severe else "現在は軽微な天候"
            future_desc = "、さらに今後悪天候が予想されています" if future_severe else ""
            
            severe_instruction = f"""
【重要】{current_desc}{future_desc}。
以下の点を最優先で考慮してください：
1. 安全確保を最優先としたアドバイスを選ぶ（特に未来の悪天候を考慮）
2. 室内での過ごし方や安全対策を推奨
3. 外出を推奨するようなアドバイスは避ける
4. 悪天候に対する適切な準備を促す
5. 【特に重要】今後悪天候が予想される場合は強い安全対策アドバイスを選択
"""
        
        # アドバイスも気象変化を考慮
        trend_advice = ""
        if state and hasattr(state, 'generation_metadata'):
            weather_trend = state.generation_metadata.get('weather_trend')
            if weather_trend:
                if weather_trend.weather_trend == "worsening" or weather_trend.precipitation_total > 10:
                    trend_advice = "\n4. 今後の悪天候に備えた準備系のアドバイスを優先"
                elif weather_trend.temperature_trend == "worsening":
                    config = get_comment_config()
                    if weather_trend.max_temperature > config.heat_warning_threshold:
                        trend_advice = "\n4. 今後の高温に備えた熱中症対策系のアドバイスを優先"
                
        # 設定から温度閾値を取得
        config = get_comment_config()
        heat_threshold = config.heat_warning_threshold
        cold_threshold = config.cold_warning_threshold
        
        # 特殊気象条件の優先基準（アドバイス用）
        special_criteria = ""
        if weather_data.weather_condition.is_special_condition:
            special_criteria = f"\n\n【最優先】{weather_data.weather_condition.value}に関連するアドバイスを選択："
            if weather_data.weather_condition.value == "thunder":
                special_criteria += "\n   - 「雷雨に注意」「屋内へ避難」「急な雷雨に注意」などの安全対策"
            elif weather_data.weather_condition.value == "fog":
                special_criteria += "\n   - 「視界不良に注意」「運転注意」「霧の可能性」などの安全対策"
            elif weather_data.weather_condition.value == "storm":
                special_criteria += "\n   - 「強風に注意」「外出を控える」「嵐の可能性」などの安全対策"
            elif weather_data.weather_condition.value == "extreme_heat":
                special_criteria += "\n   - 「熱中症に注意」「水分補給」「猛暑に警戒」などの安全対策"
            elif weather_data.weather_condition.value == "severe_storm":
                special_criteria += "\n   - 「大雨に警戒」「外出危険」「嵐に備える」などの安全対策"
        
        # 悪天候時のアドバイス基準を追加
        severe_weather_advice = ""
        if any(severe in weather_data.weather_description.lower() for severe in ["大雨", "豪雨", "嵐", "暴風", "台風", "雷"]):
            severe_weather_advice = f"""

【重要】悪天候時のアドバイス基準:
⚠️ 現在は「{weather_data.weather_description}」という危険な天候です
- 「外出注意」「安全第一」「傘必携」などの安全対策を最優先
- 「散歩」「お出かけ」「ピクニック」などの外出推奨は絶対に避ける
- 悪天候に適した準備・対策のアドバイスを選択"""

        base += f"""{severe_instruction}{special_criteria}{severe_weather_advice}

選択基準:
1. 【最優先】悪天候時は安全対策・注意喚起のアドバイス
2. 気温による除外（{weather_data.temperature}°C）：
   - {heat_threshold}°C未満で「熱中症」系は選択禁止
   - {cold_threshold}°C以上で「防寒」系は選択禁止
3. 天気条件への適切性（雨なら濡れ対策等、嵐なら外出控える等）
4. 実用的で具体的なアドバイス{trend_advice}

**重要**: 現在{weather_data.temperature}°Cなので、熱中症関連は{'選択禁止' if weather_data.temperature < heat_threshold else '選択可能'}です。"""

    return base + f"\n\n必ず候補から1つ選び、index (0〜{len(candidates)-1}) を半角数字のみで答えてください。"