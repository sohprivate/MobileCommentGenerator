"""
プロンプトビルダー - コメント生成用プロンプト構築

このモジュールは、天気情報と過去コメントを基に、
効果的な天気コメント生成用プロンプトを構築します。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """プロンプトテンプレート"""
    base_template: str
    weather_specific: Dict[str, str]
    seasonal_adjustments: Dict[str, str]
    time_specific: Dict[str, str]


class CommentPromptBuilder:
    """コメント生成用プロンプトビルダー"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> PromptTemplate:
        """プロンプトテンプレートを読み込み"""
        base_template = """あなたは天気コメント生成の専門家です。以下の情報を基に、15文字以内の適切な天気コメントを生成してください。

## 現在の天気情報
- 地点: {location}
- 天気: {weather_description}
- 気温: {temperature}°C
- 湿度: {humidity}%
- 風速: {wind_speed}m/s
- 時刻: {current_time}

## 過去の類似コメント例
{past_comments_examples}

## 生成条件
- 15文字以内（必須）
- 丁寧語で自然な表現
- 天気状況に適した内容
- 不適切な表現は避ける
- その場にいる人に向けた親しみやすい表現

## 出力形式
コメント本文のみを出力してください。説明や余計な文字は不要です。

天気コメント:"""

        weather_specific = {
            '晴れ': """
- 晴天の爽やかさを表現
- 外出や活動への前向きなメッセージ
- 日差しの強さに応じた注意喚起""",
            
            '曇り': """
- 過ごしやすい天候への言及
- 落ち着いた雰囲気の表現
- 急な天候変化への軽い注意""",
            
            '雨': """
- 雨の日の魅力や心地よさ
- 濡れ対策の軽やかな提案
- 室内で過ごす時間の価値""",
            
            '雪': """
- 雪景色の美しさや特別感
- 寒さ対策の温かい提案
- 雪の日ならではの楽しみ"""
        }
        
        seasonal_adjustments = {
            '春': '新緑や花々の季節感を含める',
            '夏': '暑さ対策や夏の楽しみを含める',
            '秋': '紅葉や涼しさの心地よさを含める',
            '冬': '寒さ対策や温かみのある表現'
        }
        
        time_specific = {
            '朝': 'おはようの挨拶や一日の始まりの表現',
            '昼': '日中の活動や明るさの表現',
            '夕方': '一日の終わりや夕焼けの表現',
            '夜': 'お疲れさまや夜の静けさの表現'
        }
        
        return PromptTemplate(
            base_template=base_template,
            weather_specific=weather_specific,
            seasonal_adjustments=seasonal_adjustments,
            time_specific=time_specific
        )
    
    def build_prompt(
        self,
        weather_data,
        past_comments: List = None,
        location: str = "",
        selected_pair = None
    ) -> str:
        """
        コメント生成用プロンプトを構築
        
        Args:
            weather_data: 天気予報データ
            past_comments: 過去コメントリスト
            location: 地点名
            selected_pair: 選択されたコメントペア
            
        Returns:
            str: 構築されたプロンプト
        """
        try:
            # 基本情報の取得
            weather_info = self._extract_weather_info(weather_data)
            past_examples = self._format_past_comments(past_comments, selected_pair)
            
            # 天気条件に応じた追加指示
            weather_guidance = self._get_weather_specific_guidance(weather_info['weather_description'])
            
            # 季節・時刻に応じた調整
            seasonal_guidance = self._get_seasonal_guidance(weather_info['current_time'])
            time_guidance = self._get_time_specific_guidance(weather_info['current_time'])
            
            # プロンプト構築
            prompt = self.templates.base_template.format(
                location=location or weather_info.get('location', ''),
                weather_description=weather_info['weather_description'],
                temperature=weather_info['temperature'],
                humidity=weather_info['humidity'],
                wind_speed=weather_info['wind_speed'],
                current_time=weather_info['current_time'],
                past_comments_examples=past_examples
            )
            
            # 追加指示を追加
            if weather_guidance:
                prompt += f"\n\n## 天気別の留意点\n{weather_guidance}"
            
            if seasonal_guidance:
                prompt += f"\n\n## 季節の表現\n{seasonal_guidance}"
            
            if time_guidance:
                prompt += f"\n\n## 時間帯の表現\n{time_guidance}"
            
            logger.debug(f"プロンプト構築完了 - 長さ: {len(prompt)}文字")
            return prompt
            
        except Exception as e:
            logger.error(f"プロンプト構築エラー: {str(e)}")
            return self._get_fallback_prompt(location, weather_data)
    
    def _extract_weather_info(self, weather_data) -> Dict[str, Any]:
        """天気データから情報を抽出"""
        if not weather_data:
            return {
                'weather_description': '不明',
                'temperature': '不明',
                'humidity': '不明',
                'wind_speed': '不明',
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        
        return {
            'location': getattr(weather_data, 'location', ''),
            'weather_description': getattr(weather_data, 'weather_description', '不明'),
            'temperature': getattr(weather_data, 'temperature', '不明'),
            'humidity': getattr(weather_data, 'humidity', '不明'),
            'wind_speed': getattr(weather_data, 'wind_speed', '不明'),
            'current_time': getattr(weather_data, 'datetime', datetime.now()).strftime('%Y-%m-%d %H:%M')
        }
    
    def _format_past_comments(self, past_comments: List, selected_pair) -> str:
        """過去コメントをフォーマット"""
        if not past_comments and not selected_pair:
            return "（過去の類似コメントなし）"
        
        examples = []
        
        # 選択されたペアを優先的に表示
        if selected_pair:
            if hasattr(selected_pair, 'weather_comment'):
                examples.append(f"- {selected_pair.weather_comment.comment_text}（天気コメント）")
            if hasattr(selected_pair, 'advice_comment'):
                examples.append(f"- {selected_pair.advice_comment.comment_text}（アドバイス）")
        
        # その他の過去コメント
        if past_comments:
            for comment in past_comments[:3]:  # 最大3件まで
                comment_text = getattr(comment, 'comment_text', str(comment))
                comment_type = getattr(comment, 'comment_type', 'unknown')
                examples.append(f"- {comment_text}（{comment_type}）")
        
        return "\n".join(examples) if examples else "（過去の類似コメントなし）"
    
    def _get_weather_specific_guidance(self, weather_description: str) -> str:
        """天気条件に応じた指示を取得"""
        for condition, guidance in self.templates.weather_specific.items():
            if condition in weather_description:
                return guidance
        return ""
    
    def _get_seasonal_guidance(self, current_time: str) -> str:
        """季節に応じた指示を取得"""
        try:
            dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M')
            month = dt.month
            
            if month in [3, 4, 5]:
                season = '春'
            elif month in [6, 7, 8]:
                season = '夏'
            elif month in [9, 10, 11]:
                season = '秋'
            else:
                season = '冬'
            
            return self.templates.seasonal_adjustments.get(season, '')
        except:
            return ""
    
    def _get_time_specific_guidance(self, current_time: str) -> str:
        """時間帯に応じた指示を取得"""
        try:
            dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M')
            hour = dt.hour
            
            if 5 <= hour < 11:
                time_period = '朝'
            elif 11 <= hour < 17:
                time_period = '昼'
            elif 17 <= hour < 21:
                time_period = '夕方'
            else:
                time_period = '夜'
            
            return self.templates.time_specific.get(time_period, '')
        except:
            return ""
    
    def _get_fallback_prompt(self, location: str, weather_data) -> str:
        """フォールバック用のシンプルなプロンプト"""
        return f"""15文字以内で{location or ''}の天気に適したコメントを生成してください。
丁寧語で自然な表現にしてください。

天気コメント:"""
    
    def create_custom_prompt(
        self,
        template: str,
        weather_data,
        past_comments: List = None,
        **kwargs
    ) -> str:
        """
        カスタムテンプレートでプロンプト生成
        
        Args:
            template: カスタムテンプレート文字列
            weather_data: 天気データ
            past_comments: 過去コメント
            **kwargs: その他のパラメータ
            
        Returns:
            str: 構築されたプロンプト
        """
        weather_info = self._extract_weather_info(weather_data)
        past_examples = self._format_past_comments(past_comments, None)
        
        format_vars = {
            **weather_info,
            'past_comments_examples': past_examples,
            **kwargs
        }
        
        try:
            return template.format(**format_vars)
        except KeyError as e:
            logger.error(f"テンプレート変数不足: {str(e)}")
            return self._get_fallback_prompt(kwargs.get('location', ''), weather_data)


def create_simple_prompt(weather_description: str, temperature: str, location: str = "") -> str:
    """シンプルなプロンプト生成（テスト用）"""
    return f"""天気が{weather_description}、気温{temperature}度の{location}について、15文字以内の天気コメントを生成してください。

天気コメント:"""


# プロンプトテンプレート例
EXAMPLE_TEMPLATES = {
    'basic': """15文字以内で{location}の天気コメントを生成してください。
天気: {weather_description}
気温: {temperature}°C

天気コメント:""",
    
    'detailed': """あなたは天気キャスターです。以下の天気情報を基に、視聴者に向けた15文字以内のコメントを生成してください。

地点: {location}
天気: {weather_description}
気温: {temperature}°C
時刻: {current_time}

過去の例:
{past_comments_examples}

天気コメント:""",
    
    'friendly': """親しみやすい天気コメントを15文字以内で生成してください。

今の天気: {weather_description}
気温: {temperature}°C
場所: {location}

天気コメント:"""
}
