"""天気コメント検証システム - 天気条件に不適切なコメントを検出・除外"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from src.data.weather_data import WeatherForecast, WeatherCondition
from src.data.past_comment import PastComment, CommentType

logger = logging.getLogger(__name__)


class WeatherCommentValidator:
    """天気条件に基づいてコメントの適切性を検証"""
    
    def __init__(self):
        # 天気別禁止ワードの定義
        self.weather_forbidden_words = {
            # 雨天時（全レベル）
            "rain": {
                "weather_comment": [
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 雨天時に矛盾する表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 雨天時の生活関連アドバイスを追加
                    "洗濯物を外に", "布団を干す", "外干しを", "窓を開けて", "ベランダ作業"
                ]
            },
            # 大雨・豪雨・嵐
            "heavy_rain": {
                "weather_comment": [
                    # 雨天時の禁止ワード全て
                    "青空", "晴れ", "快晴", "日差し", "太陽", "陽射し", "眩しい",
                    "穏やか", "過ごしやすい", "快適", "爽やか", "心地良い", "のどか",
                    "お出かけ日和", "散歩日和", "ピクニック", "外出推奨",
                    "スッキリ", "気持ちいい", "清々しい",
                    # 軽微な表現（大雨時は特に禁止）
                    "にわか雨", "ニワカ雨", "変わりやすい", "スッキリしない",
                    "蒸し暑い", "厳しい暑さ", "体感", "心地",
                    "雲の多い", "どんより", "じめじめ", "湿っぽい",
                    # 大雨時に特に不適切な表現を追加
                    "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み",
                    "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下"
                ],
                "advice": [
                    # 基本的な外出系
                    "日焼け止め", "帽子", "サングラス", "日傘", "紫外線",
                    "お出かけ", "外出", "散歩", "ピクニック", "日光浴",
                    "過ごしやすい", "快適", "心地良い", "爽やか",
                    # 軽い対策（大雨時は不適切）
                    "折り畳み傘", "軽い雨具", "短時間の外出"
                ]
            },
            # 晴天時
            "sunny": {
                "weather_comment": [
                    "雨", "じめじめ", "湿った", "どんより", "曇り", "雲が厚い",
                    "傘", "雨具", "濡れ", "湿気", "降水"
                ],
                "advice": [
                    "傘", "レインコート", "濡れ", "雨具", "長靴"
                ]
            },
            # 曇天時
            "cloudy": {
                "weather_comment": [
                    "青空", "快晴", "眩しい", "強い日差し", "ギラギラ",
                    # 雨天時の生活関連表現を追加
                    "洗濯日和", "布団干し日和", "外干し", "窓を開けて", "ベランダで"
                ],
                "advice": [
                    "強い日差し対策", "紫外線対策必須"
                ]
            }
        }
        
        # 温度別禁止ワード
        self.temperature_forbidden_words = {
            "hot": {  # 30°C以上
                "forbidden": ["寒い", "冷える", "肌寒い", "防寒", "暖かく", "厚着"]
            },
            "cold": {  # 12°C未満（防寒閾値調整）
                "forbidden": ["暑い", "猛暑", "酷暑", "熱中症", "クーラー", "冷房"]
            },
            "mild": {  # 10-30°C
                "forbidden": ["極寒", "凍える", "猛暑", "酷暑"]
            }
        }
        
        # 必須キーワード（悪天候時）
        self.required_keywords = {
            "heavy_rain": {
                "weather_comment": ["注意", "警戒", "危険", "荒れ", "激しい", "強い", "本格的"],
                "advice": ["傘", "雨具", "安全", "注意", "室内", "控え", "警戒", "備え", "準備"]
            },
            "storm": {
                "weather_comment": ["嵐", "暴風", "警戒", "危険", "荒天", "大荒れ"],
                "advice": ["危険", "外出控え", "安全確保", "警戒", "室内", "備え", "準備"]
            }
        }
    
    def validate_comment(self, comment: PastComment, weather_data: WeatherForecast) -> Tuple[bool, str]:
        """
        コメントが天気条件に適しているか検証
        
        Returns:
            (is_valid, reason): 検証結果とその理由
        """
        comment_text = comment.comment_text
        comment_type = comment.comment_type.value
        
        # 1. 天気条件チェック
        weather_check = self._check_weather_conditions(comment_text, comment_type, weather_data)
        if not weather_check[0]:
            return weather_check
        
        # 2. 温度条件チェック
        temp_check = self._check_temperature_conditions(comment_text, weather_data)
        if not temp_check[0]:
            return temp_check
        
        # 2.5. 地域特性チェック（位置情報がある場合）
        if hasattr(weather_data, 'location') and weather_data.location:
            regional_check = self._check_regional_specifics(comment_text, weather_data.location)
            if not regional_check[0]:
                return regional_check
        
        # 3. 湿度条件チェック
        humidity_check = self._check_humidity_conditions(comment_text, weather_data)
        if not humidity_check[0]:
            return humidity_check
        
        # 4. 必須キーワードチェック（悪天候時）
        required_check = self._check_required_keywords(comment_text, comment_type, weather_data)
        if not required_check[0]:
            return required_check
        
        # 5. 雨天時の矛盾表現チェック
        contradiction_check = self._check_rainy_weather_contradictions(comment_text, weather_data)
        if not contradiction_check[0]:
            return contradiction_check
        
        return True, "OK"
    
    def _check_weather_conditions(self, comment_text: str, comment_type: str, 
                                 weather_data: WeatherForecast) -> Tuple[bool, str]:
        """天気条件に基づく検証"""
        weather_desc = weather_data.weather_description.lower()
        comment_lower = comment_text.lower()
        precipitation = weather_data.precipitation
        
        # 降水量レベルを取得
        precipitation_severity = weather_data.get_precipitation_severity()
        
        # 大雨・嵐チェック
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風", "台風"]):
            forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"悪天候時の禁止ワード「{word}」を含む"
        
        # 雷の特別チェック（降水量を考慮）
        elif "雷" in weather_desc:
            if precipitation >= 5.0:
                # 強い雷（降水量5mm以上）
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
                for word in forbidden_words:
                    if word in comment_text:
                        return False, f"強い雷雨時の禁止ワード「{word}」を含む"
            else:
                # 軽微な雷（降水量5mm未満）
                if comment_type == "weather_comment":
                    # 軽微な雷では強い警戒表現を禁止
                    strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
                    for word in strong_warning_words:
                        if word in comment_text:
                            return False, f"軽微な雷（{precipitation}mm）で過度な警戒表現「{word}」を含む"
                elif comment_type == "advice":
                    # 軽微な雷では強い警戒アドバイスを禁止
                    strong_warning_advice = ["避難", "危険", "中止", "延期", "控える"]
                    for word in strong_warning_advice:
                        if word in comment_text:
                            return False, f"軽微な雷（{precipitation}mm）で過度な警戒アドバイス「{word}」を含む"
        
        # 通常の雨チェック（降水量レベルで判定）
        elif any(rain in weather_desc for rain in ["雨", "rain"]):
            if precipitation_severity in ["heavy", "very_heavy"]:
                # 大雨・激しい雨
                forbidden_words = self.weather_forbidden_words["heavy_rain"][comment_type]
            else:
                # 軽い雨～中程度の雨
                forbidden_words = self.weather_forbidden_words["rain"][comment_type]
            
            for word in forbidden_words:
                if word in comment_text:
                    severity_desc = "大雨" if precipitation_severity in ["heavy", "very_heavy"] else "雨天"
                    return False, f"{severity_desc}時の禁止ワード「{word}」を含む"
            
            # 軽い雨では強い警戒表現を禁止
            if precipitation_severity == "light" and comment_type == "weather_comment":
                strong_warning_words = ["激しい", "警戒", "危険", "大荒れ", "本格的", "強雨"]
                for word in strong_warning_words:
                    if word in comment_text:
                        return False, f"軽い雨（{precipitation}mm）で過度な警戒表現「{word}」を含む"
        
        # 晴天チェック
        elif any(sunny in weather_desc for sunny in ["晴", "快晴"]):
            forbidden_words = self.weather_forbidden_words["sunny"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"晴天時の禁止ワード「{word}」を含む"
        
        # 曇天チェック
        elif "曇" in weather_desc or "くもり" in weather_desc:
            forbidden_words = self.weather_forbidden_words["cloudy"][comment_type]
            for word in forbidden_words:
                if word in comment_text:
                    return False, f"曇天時の禁止ワード「{word}」を含む"
            
            # 曇天時に「スッキリしない」を許可（除外から除く）
            if "スッキリしない" in comment_text:
                return True, "曇天時の適切な表現"
        
        return True, "天気条件OK"
    
    def _check_temperature_conditions(self, comment_text: str, 
                                    weather_data: WeatherForecast) -> Tuple[bool, str]:
        """温度条件に基づく検証"""
        temp = weather_data.temperature
        
        if temp >= 30:
            forbidden = self.temperature_forbidden_words["hot"]["forbidden"]
        elif temp < 12:
            forbidden = self.temperature_forbidden_words["cold"]["forbidden"]
        else:
            forbidden = self.temperature_forbidden_words["mild"]["forbidden"]
        
        for word in forbidden:
            if word in comment_text:
                return False, f"温度{temp}°Cで禁止ワード「{word}」を含む"
        
        return True, "温度条件OK"
    
    def _check_humidity_conditions(self, comment_text: str, 
                                  weather_data: WeatherForecast) -> Tuple[bool, str]:
        """湿度条件に基づく検証"""
        humidity = weather_data.humidity
        
        # 高湿度時（80%以上）の乾燥関連コメントを除外
        if humidity >= 80:
            dry_words = ["乾燥注意", "乾燥対策", "乾燥しやすい", "乾燥した空気", 
                        "からっと", "さっぱり", "湿度低下"]
            for word in dry_words:
                if word in comment_text:
                    return False, f"高湿度（{humidity}%）で乾燥関連表現「{word}」を含む"
        
        # 低湿度時（30%未満）の除湿関連コメントを除外
        if humidity < 30:
            humid_words = ["除湿対策", "除湿", "ジメジメ", "湿気対策", "湿っぽい"]
            for word in humid_words:
                if word in comment_text:
                    return False, f"低湿度（{humidity}%）で除湿関連表現「{word}」を含む"
        
        return True, "湿度条件OK"
    
    def _check_required_keywords(self, comment_text: str, comment_type: str,
                                weather_data: WeatherForecast) -> Tuple[bool, str]:
        """必須キーワードチェック（悪天候時）"""
        weather_desc = weather_data.weather_description.lower()
        
        # 大雨・豪雨時
        if any(heavy in weather_desc for heavy in ["大雨", "豪雨"]):
            if comment_type in self.required_keywords["heavy_rain"]:
                required = self.required_keywords["heavy_rain"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"大雨時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        # 嵐・暴風時
        elif any(storm in weather_desc for storm in ["嵐", "暴風", "台風"]):
            if comment_type in self.required_keywords["storm"]:
                required = self.required_keywords["storm"][comment_type]
                if not any(keyword in comment_text for keyword in required):
                    return False, f"嵐時の必須キーワード不足（{', '.join(required)}のいずれか必要）"
        
        return True, "必須キーワードOK"
    
    def _check_rainy_weather_contradictions(self, comment_text: str, 
                                          weather_data: WeatherForecast) -> Tuple[bool, str]:
        """雨天時の矛盾表現を特別にチェック"""
        weather_desc = weather_data.weather_description.lower()
        
        # 雨天チェック
        if any(rain_word in weather_desc for rain_word in ["雨", "小雨", "中雨", "大雨", "豪雨"]):
            # 雨天時に矛盾する表現のリスト
            contradictory_phrases = [
                "中休み", "晴れ間", "回復", "一時的な晴れ", "梅雨の中休み", 
                "梅雨明け", "からっと", "さっぱり", "乾燥", "湿度低下",
                "晴天", "好天", "快晴の", "青空が"
            ]
            
            for phrase in contradictory_phrases:
                if phrase in comment_text:
                    return False, f"雨天時の矛盾表現「{phrase}」を含む（天気：{weather_data.weather_description}）"
        
        return True, "矛盾表現チェックOK"
    
    def _check_regional_specifics(self, comment_text: str, location: str) -> Tuple[bool, str]:
        """地域特性に基づく検証"""
        # 沖縄特有のチェック
        if "沖縄" in location:
            # 雪関連のコメントを除外
            snow_words = ["雪", "雪景色", "粉雪", "新雪", "雪かき", "雪道", "雪が降る"]
            for word in snow_words:
                if word in comment_text:
                    return False, f"沖縄で雪関連表現「{word}」は不適切"
            
            # 低温警告の闾値を緩和（沖縄は寒くならない）
            strong_cold_words = ["極寒", "凍える", "凍結", "防寒対策必須"]
            for word in strong_cold_words:
                if word in comment_text:
                    return False, f"沖縄で強い寒さ表現「{word}」は不適切"
        
        # 北海道特有のチェック
        elif "北海道" in location:
            # 高温警告の闾値を上げ（北海道は暑くなりにくい）
            strong_heat_words = ["酷暑", "猛暑", "危険な暑さ", "熱帯夜"]
            for word in strong_heat_words:
                if word in comment_text:
                    return False, f"北海道で強い暑さ表現「{word}」は不適切"
        
        return True, "地域特性OK"
    
    def filter_comments(self, comments: List[PastComment], 
                       weather_data: WeatherForecast) -> List[PastComment]:
        """
        コメントリストから不適切なものを除外
        
        Returns:
            適切なコメントのみのリスト
        """
        valid_comments = []
        
        for comment in comments:
            is_valid, reason = self.validate_comment(comment, weather_data)
            if is_valid:
                valid_comments.append(comment)
            else:
                logger.info(f"コメント除外: '{comment.comment_text}' - 理由: {reason}")
        
        # 有効なコメントが少なすぎる場合の警告
        if len(valid_comments) < len(comments) * 0.1:  # 90%以上除外された場合
            logger.warning(f"大量のコメントが除外されました: {len(comments)}件中{len(valid_comments)}件のみ有効")
        
        return valid_comments
    
    def get_weather_appropriate_comments(self, comments: List[PastComment],
                                       weather_data: WeatherForecast,
                                       comment_type: CommentType,
                                       limit: int = 30) -> List[PastComment]:
        """
        天気に最も適したコメントを優先順位付けして取得
        
        Returns:
            優先順位付けされたコメントリスト（最大limit件）
        """
        # まず不適切なコメントを除外
        valid_comments = self.filter_comments(comments, weather_data)
        
        # スコアリング
        scored_comments = []
        for comment in valid_comments:
            score = self._calculate_appropriateness_score(comment, weather_data)
            scored_comments.append((score, comment))
        
        # スコア順にソート
        scored_comments.sort(key=lambda x: x[0], reverse=True)
        
        # 上位limit件を返す
        return [comment for _, comment in scored_comments[:limit]]
    
    def _calculate_appropriateness_score(self, comment: PastComment, 
                                       weather_data: WeatherForecast) -> float:
        """コメントの適切性スコアを計算"""
        score = 100.0  # 基本スコア
        comment_text = comment.comment_text
        weather_desc = weather_data.weather_description.lower()
        
        # 悪天候時のスコアリング
        if any(severe in weather_desc for severe in ["大雨", "豪雨", "嵐", "暴風"]):
            # 強い警戒表現にボーナス
            strong_warning_words = ["警戒", "危険", "激しい", "本格的", "荒れ", "大荒れ"]
            for word in strong_warning_words:
                if word in comment_text:
                    score += 20.0
            
            # 軽い表現にペナルティ
            mild_words = ["にわか雨", "変わりやすい", "スッキリしない", "どんより"]
            for word in mild_words:
                if word in comment_text:
                    score -= 30.0
        
        # 季節との一致度
        if 'season' in comment.raw_data:
            current_month = weather_data.datetime.month
            expected_season = self._get_season_from_month(current_month)
            if comment.raw_data['season'] == expected_season:
                score += 10.0
        
        # 使用回数によるスコア（人気度）
        if 'count' in comment.raw_data:
            count = comment.raw_data['count']
            score += min(count / 1000, 10.0)  # 最大10点のボーナス
        
        return score
    
    def _get_season_from_month(self, month: int) -> str:
        """月から季節を判定"""
        if month in [3, 4, 5]:
            return "春"
        elif month == 6:
            return "梅雨"
        elif month in [7, 8]:
            return "夏"
        elif month == 9:
            return "台風"
        elif month in [10, 11]:
            return "秋"
        else:  # 12, 1, 2
            return "冬"