"""
コメント候補評価エンジン

コメントの品質を多角的に評価する機能
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import logging
from datetime import datetime

from src.data.evaluation_criteria import (
    EvaluationCriteria,
    CriterionScore,
    EvaluationResult,
    EvaluationContext,
    DEFAULT_CRITERION_WEIGHTS
)
from src.data.comment_pair import CommentPair
from src.data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class CommentEvaluator:
    """
    コメント候補を評価するクラス
    """
    
    # 不適切な表現パターン
    INAPPROPRIATE_PATTERNS = [
        r'死|殺|自殺',
        r'バカ|アホ|クソ',
        r'最悪|地獄|絶望',
        r'危険|警告|注意(?!を)'  # 「注意を」は除外
    ]
    
    # ポジティブな表現
    POSITIVE_EXPRESSIONS = [
        '素敵', '素晴らしい', '快適', '爽やか', '心地よい',
        '楽しい', '嬉しい', '幸せ', '最高', 'いい天気'
    ]
    
    # エンゲージメント要素
    ENGAGEMENT_ELEMENTS = [
        r'[!！♪☆★]',  # 感嘆符や装飾
        r'〜|～',  # 波線
        r'ね[。！]?$',  # 語尾の「ね」
        r'よ[。！]?$',  # 語尾の「よ」
        r'でしょう[。！]?$'  # 語尾の「でしょう」
    ]
    
    def __init__(self, weights: Optional[Dict[EvaluationCriteria, float]] = None):
        """
        初期化
        
        Args:
            weights: 評価基準の重み（Noneの場合はデフォルト使用）
        """
        self.weights = weights or DEFAULT_CRITERION_WEIGHTS.copy()
        self._compile_patterns()
    
    def _compile_patterns(self):
        """正規表現パターンをコンパイル"""
        self.inappropriate_regex = re.compile(
            '|'.join(self.INAPPROPRIATE_PATTERNS),
            re.IGNORECASE
        )
        self.engagement_regex = re.compile(
            '|'.join(self.ENGAGEMENT_ELEMENTS)
        )
    
    def evaluate_comment_pair(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> EvaluationResult:
        """
        コメントペアを評価
        
        Args:
            comment_pair: 評価対象のコメントペア
            context: 評価コンテキスト
            weather_data: 天気データ
            
        Returns:
            評価結果
        """
        criterion_scores = []
        
        # 各評価基準でスコアリング
        for criterion in EvaluationCriteria:
            score = self._evaluate_criterion(
                criterion,
                comment_pair,
                context,
                weather_data
            )
            criterion_scores.append(score)
        
        # 総合スコアを計算
        total_score = self._calculate_total_score(criterion_scores)
        
        # 検証結果を判定
        is_valid = self._determine_validity(criterion_scores, total_score)
        
        # 改善提案を生成
        suggestions = self._generate_suggestions(criterion_scores, comment_pair)
        
        # 評価結果を作成
        result = EvaluationResult(
            is_valid=is_valid,
            total_score=total_score,
            criterion_scores=criterion_scores,
            suggestions=suggestions,
            metadata={
                "evaluated_at": datetime.now().isoformat(),
                "weather_condition": weather_data.weather_description,
                "location": context.location
            }
        )
        
        return result
    
    def _evaluate_criterion(
        self,
        criterion: EvaluationCriteria,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """個別の評価基準でスコアリング"""
        
        evaluators = {
            EvaluationCriteria.RELEVANCE: self._evaluate_relevance,
            EvaluationCriteria.CREATIVITY: self._evaluate_creativity,
            EvaluationCriteria.NATURALNESS: self._evaluate_naturalness,
            EvaluationCriteria.APPROPRIATENESS: self._evaluate_appropriateness,
            EvaluationCriteria.ENGAGEMENT: self._evaluate_engagement,
            EvaluationCriteria.CLARITY: self._evaluate_clarity,
            EvaluationCriteria.CONSISTENCY: self._evaluate_consistency,
            EvaluationCriteria.ORIGINALITY: self._evaluate_originality
        }
        
        evaluator = evaluators.get(criterion)
        if not evaluator:
            logger.warning(f"評価基準 {criterion} の評価器が見つかりません")
            return CriterionScore(
                criterion=criterion,
                score=0.5,
                weight=self.weights.get(criterion, 1.0),
                reason="評価器が未実装"
            )
        
        return evaluator(comment_pair, context, weather_data)
    
    def _evaluate_relevance(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """関連性を評価"""
        score = 0.0
        reasons = []
        
        # 天気条件との一致
        weather_comment = comment_pair.weather_comment.comment_text
        weather_desc = weather_data.weather_description
        
        if weather_desc in weather_comment:
            score += 0.4
            reasons.append("天気条件が直接言及されている")
        elif self._is_weather_related(weather_comment, weather_desc):
            score += 0.2
            reasons.append("天気条件と関連性がある")
        
        # 気温との関連性
        temp = weather_data.temperature
        if self._is_temperature_relevant(weather_comment, temp):
            score += 0.3
            reasons.append(f"気温（{temp}度）に適した表現")
        
        # 時間帯との関連性
        hour = context.target_datetime.hour
        if self._is_time_relevant(weather_comment, hour):
            score += 0.2
            reasons.append("時間帯に適した表現")
        
        # アドバイスの適切性
        advice = comment_pair.advice_comment.comment_text
        if self._is_advice_relevant(advice, weather_desc, temp):
            score += 0.1
            reasons.append("アドバイスが状況に適している")
        
        return CriterionScore(
            criterion=EvaluationCriteria.RELEVANCE,
            score=min(score, 1.0),
            weight=self.weights[EvaluationCriteria.RELEVANCE],
            reason="、".join(reasons) if reasons else "関連性が低い"
        )
    
    def _evaluate_creativity(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """創造性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text
        
        score = 0.0
        reasons = []
        
        # 比喩や擬人化の使用
        if self._has_metaphor(weather_text):
            score += 0.3
            reasons.append("比喩表現を使用")
        
        # 独創的な表現
        if self._is_unique_expression(weather_text):
            score += 0.3
            reasons.append("独創的な表現")
        
        # 感情的な要素
        if self._has_emotional_element(weather_text):
            score += 0.2
            reasons.append("感情を込めた表現")
        
        # 予想外のアドバイス
        if self._is_creative_advice(advice_text):
            score += 0.2
            reasons.append("創造的なアドバイス")
        
        return CriterionScore(
            criterion=EvaluationCriteria.CREATIVITY,
            score=min(score, 1.0),
            weight=self.weights[EvaluationCriteria.CREATIVITY],
            reason="、".join(reasons) if reasons else "標準的な表現"
        )
    
    def _evaluate_naturalness(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """自然さを評価"""
        weather_text = comment_pair.weather_comment.comment_text
        
        score = 1.0  # 減点方式
        reasons = []
        
        # 文法的な違和感
        if self._has_grammatical_issues(weather_text):
            score -= 0.3
            reasons.append("文法的な違和感あり")
        
        # 不自然な敬語
        if self._has_unnatural_honorifics(weather_text):
            score -= 0.2
            reasons.append("敬語が不自然")
        
        # 口語的すぎる/堅すぎる
        tone_score = self._evaluate_tone_balance(weather_text)
        if tone_score < 0.5:
            score -= 0.2
            reasons.append("トーンバランスが不適切")
        
        # 文の長さ
        if len(weather_text) > 50 or len(weather_text) < 5:
            score -= 0.1
            reasons.append("文の長さが不適切")
        
        return CriterionScore(
            criterion=EvaluationCriteria.NATURALNESS,
            score=max(score, 0.0),
            weight=self.weights[EvaluationCriteria.NATURALNESS],
            reason="、".join(reasons) if reasons else "自然な表現"
        )
    
    def _evaluate_appropriateness(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """適切性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text
        
        score = 1.0  # 減点方式
        reasons = []
        
        # 不適切な表現チェック
        if self.inappropriate_regex.search(weather_text) or \
           self.inappropriate_regex.search(advice_text):
            score -= 0.5
            reasons.append("不適切な表現を含む")
        
        # ネガティブすぎる表現
        if self._is_too_negative(weather_text):
            score -= 0.3
            reasons.append("過度にネガティブ")
        
        # 状況に不適切なアドバイス
        if not self._is_advice_appropriate(advice_text, weather_data):
            score -= 0.2
            reasons.append("状況に不適切なアドバイス")
        
        return CriterionScore(
            criterion=EvaluationCriteria.APPROPRIATENESS,
            score=max(score, 0.0),
            weight=self.weights[EvaluationCriteria.APPROPRIATENESS],
            reason="、".join(reasons) if reasons else "適切な内容"
        )
    
    def _evaluate_engagement(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """エンゲージメントを評価"""
        weather_text = comment_pair.weather_comment.comment_text
        
        score = 0.0
        reasons = []
        
        # エンゲージメント要素の存在
        if self.engagement_regex.search(weather_text):
            score += 0.3
            reasons.append("親しみやすい表現要素")
        
        # ポジティブな表現
        positive_count = sum(1 for expr in self.POSITIVE_EXPRESSIONS if expr in weather_text)
        if positive_count > 0:
            score += min(0.3 * positive_count, 0.4)
            reasons.append("ポジティブな表現を使用")
        
        # 共感を誘う表現
        if self._has_empathy_element(weather_text):
            score += 0.3
            reasons.append("共感を誘う表現")
        
        return CriterionScore(
            criterion=EvaluationCriteria.ENGAGEMENT,
            score=min(score, 1.0),
            weight=self.weights[EvaluationCriteria.ENGAGEMENT],
            reason="、".join(reasons) if reasons else "標準的なエンゲージメント"
        )
    
    def _evaluate_clarity(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """明確性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text
        
        score = 1.0  # 減点方式
        reasons = []
        
        # 曖昧な表現
        if self._has_ambiguous_expression(weather_text):
            score -= 0.3
            reasons.append("曖昧な表現あり")
        
        # 主語の欠如
        if not self._has_clear_subject(weather_text):
            score -= 0.2
            reasons.append("主語が不明確")
        
        # アドバイスの具体性
        if not self._is_advice_specific(advice_text):
            score -= 0.2
            reasons.append("アドバイスが抽象的")
        
        return CriterionScore(
            criterion=EvaluationCriteria.CLARITY,
            score=max(score, 0.0),
            weight=self.weights[EvaluationCriteria.CLARITY],
            reason="、".join(reasons) if reasons else "明確な表現"
        )
    
    def _evaluate_consistency(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """一貫性を評価"""
        weather_text = comment_pair.weather_comment.comment_text
        advice_text = comment_pair.advice_comment.comment_text
        
        score = 1.0
        reasons = []
        
        # トーンの一貫性
        if not self._has_consistent_tone(weather_text, advice_text):
            score -= 0.5
            reasons.append("トーンが不一致")
        
        # 内容の矛盾
        if self._has_contradiction(weather_text, advice_text):
            score -= 0.5
            reasons.append("内容に矛盾あり")
        
        return CriterionScore(
            criterion=EvaluationCriteria.CONSISTENCY,
            score=max(score, 0.0),
            weight=self.weights[EvaluationCriteria.CONSISTENCY],
            reason="、".join(reasons) if reasons else "一貫性あり"
        )
    
    def _evaluate_originality(
        self,
        comment_pair: CommentPair,
        context: EvaluationContext,
        weather_data: WeatherForecast
    ) -> CriterionScore:
        """オリジナリティを評価"""
        weather_text = comment_pair.weather_comment.comment_text
        
        # 簡易的な実装（実際は過去データとの比較が必要）
        common_phrases = ["いい天気", "雨ですね", "寒いです", "暑いです"]
        
        score = 0.8  # ベーススコア
        if any(phrase in weather_text for phrase in common_phrases):
            score = 0.3
            reason = "一般的な表現"
        else:
            reason = "独自性のある表現"
        
        return CriterionScore(
            criterion=EvaluationCriteria.ORIGINALITY,
            score=score,
            weight=self.weights[EvaluationCriteria.ORIGINALITY],
            reason=reason
        )
    
    # ヘルパーメソッド
    
    def _calculate_total_score(self, criterion_scores: List[CriterionScore]) -> float:
        """総合スコアを計算"""
        total_weighted = sum(score.weighted_score for score in criterion_scores)
        total_weight = sum(score.weight for score in criterion_scores)
        return total_weighted / total_weight if total_weight > 0 else 0.0
    
    def _determine_validity(
        self,
        criterion_scores: List[CriterionScore],
        total_score: float
    ) -> bool:
        """検証結果を判定"""
        # 総合スコアが閾値以上
        if total_score < 0.6:
            return False
        
        # 重要な基準で低スコアがないか
        critical_criteria = [
            EvaluationCriteria.APPROPRIATENESS,
            EvaluationCriteria.RELEVANCE
        ]
        
        for criterion in critical_criteria:
            score = next((s for s in criterion_scores if s.criterion == criterion), None)
            if score and score.score < 0.5:
                return False
        
        return True
    
    def _generate_suggestions(
        self,
        criterion_scores: List[CriterionScore],
        comment_pair: CommentPair
    ) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        # 低スコアの基準に対する提案
        for score in criterion_scores:
            if score.score < 0.5:
                suggestion = self._get_suggestion_for_criterion(
                    score.criterion,
                    score.score,
                    comment_pair
                )
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _get_suggestion_for_criterion(
        self,
        criterion: EvaluationCriteria,
        score: float,
        comment_pair: CommentPair
    ) -> Optional[str]:
        """基準別の改善提案"""
        suggestions_map = {
            EvaluationCriteria.RELEVANCE: "天気条件や気温により適した表現を使用してください",
            EvaluationCriteria.CREATIVITY: "比喩や感情表現を加えてより創造的にしてください",
            EvaluationCriteria.NATURALNESS: "より自然な日本語表現を心がけてください",
            EvaluationCriteria.APPROPRIATENESS: "不適切な表現を避け、ポジティブな内容にしてください",
            EvaluationCriteria.ENGAGEMENT: "親しみやすい表現や装飾を追加してください",
            EvaluationCriteria.CLARITY: "より具体的で明確な表現を使用してください",
            EvaluationCriteria.CONSISTENCY: "天気コメントとアドバイスのトーンを統一してください",
            EvaluationCriteria.ORIGINALITY: "より独自性のある表現を考えてください"
        }
        
        return suggestions_map.get(criterion)
    
    # 評価用ユーティリティメソッド（一部抜粋）
    
    def _is_weather_related(self, text: str, weather: str) -> bool:
        """天気関連の表現かチェック"""
        weather_keywords = {
            "晴れ": ["晴", "日差し", "青空", "太陽"],
            "曇り": ["曇", "雲", "どんより", "グレー"],
            "雨": ["雨", "傘", "濡れ", "しっとり"],
            "雪": ["雪", "白", "積も", "寒"]
        }
        
        for key, keywords in weather_keywords.items():
            if key in weather:
                return any(kw in text for kw in keywords)
        return False
    
    def _is_temperature_relevant(self, text: str, temp: float) -> bool:
        """気温に適した表現かチェック"""
        if temp < 10:
            cold_words = ["寒", "冷", "凍", "ひんやり", "冷え"]
            return any(word in text for word in cold_words)
        elif temp > 25:
            hot_words = ["暑", "熱", "汗", "蒸し", "夏"]
            return any(word in text for word in hot_words)
        else:
            mild_words = ["過ごしやすい", "快適", "心地よい", "爽やか"]
            return any(word in text for word in mild_words)
    
    def _is_time_relevant(self, text: str, hour: int) -> bool:
        """時間帯に適した表現かチェック"""
        if 5 <= hour < 10:
            return any(word in text for word in ["朝", "おはよう", "目覚め"])
        elif 10 <= hour < 17:
            return any(word in text for word in ["昼", "日中", "午後"])
        elif 17 <= hour < 21:
            return any(word in text for word in ["夕", "夜", "日暮れ"])
        else:
            return any(word in text for word in ["夜", "星", "月"])
    
    def _has_metaphor(self, text: str) -> bool:
        """比喩表現を含むかチェック"""
        metaphor_patterns = ["ような", "みたい", "らしい", "のよう"]
        return any(pattern in text for pattern in metaphor_patterns)
    
    def _is_too_negative(self, text: str) -> bool:
        """過度にネガティブかチェック"""
        negative_words = ["最悪", "地獄", "つらい", "苦しい", "嫌", "ダメ"]
        return sum(1 for word in negative_words if word in text) >= 2
    
    def _has_empathy_element(self, text: str) -> bool:
        """共感要素を含むかチェック"""
        empathy_patterns = ["ですね", "でしょう", "ますよね", "かもしれません"]
        return any(pattern in text for pattern in empathy_patterns)
