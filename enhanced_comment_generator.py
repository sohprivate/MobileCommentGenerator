import json
import os
from collections import Counter, defaultdict
from typing import Dict, List, Set, Optional

import boto3
import pandas as pd

# 🔑 AWSプロファイル名を環境変数から取得（デフォルト: dit-training）
aws_profile = os.getenv("AWS_PROFILE", "dit-training")
session = boto3.Session(profile_name=aws_profile)
s3 = session.client("s3")

# 📂 S3バケット情報
BUCKET = "it-literacy-457604437098-ap-northeast-1"
PREFIX = "downloaded_jsonl_files_archive/"

# 🗃 出力フォルダを作成
os.makedirs("output", exist_ok=True)


# 🗓 カテゴリ分類関数
def classify_category(yyyymm: str) -> str:
    month = int(yyyymm[4:])
    if month in [3, 4, 5]:
        return "春"
    if month == 6:
        return "梅雨"
    if month in [7, 8]:
        return "夏"
    if month == 9:
        return "台風"
    if month in [10, 11]:
        return "秋"
    if month in [12, 1, 2]:
        return "冬"
    return "不明"


# 🎯 天候パターン分析器
class WeatherPatternAnalyzer:
    def __init__(self):
        # 天候パターン定義
        self.patterns = {
            "sunny": ["晴", "陽", "日差し", "太陽", "青空", "快晴", "好天", "日射", "眩し", "まぶし"],
            "cloudy": ["雲", "曇", "どんより", "厚雲", "薄雲", "雲間", "雲海"],
            "rainy": ["雨", "傘", "濡れ", "湿", "じめじめ", "しとしと", "ザーザー", "ぽつぽつ", "降水", "レイン"],
            "stormy": ["雷", "雷雨", "突風", "暴風", "嵐", "荒天", "強風", "ゲリラ", "竜巻"],
            "mixed": ["変わり", "移ろ", "変化", "不安定", "ころころ", "たり", "一時", "のち"],
            "fog": ["霧", "もや", "かすみ", "霞", "視界", "靄", "ミスト"],
            "snow": ["雪", "雪化粧", "粉雪", "吹雪", "雪降", "積雪", "雪景色"],
            "hot": ["暑", "猛暑", "酷暑", "炎天", "熱中", "灼熱", "蒸し暑", "真夏日"],
            "cold": ["寒", "冷", "凍", "氷", "霜", "極寒", "厳寒", "真冬日"],
            "humid": ["湿", "ムシムシ", "じめじめ", "べたべた", "蒸し", "湿気"],
            "dry": ["乾燥", "カラカラ", "パサパサ", "乾い", "湿度低"],
            "wind": ["風", "そよ風", "微風", "強風", "突風", "無風", "風速", "ビル風"],
            "special": ["黄砂", "花粉", "紫外線", "UV", "オゾン", "PM2.5", "大気"],
        }

    def analyze_comment(self, comment: str) -> Dict[str, bool]:
        """コメントの天候パターンを分析"""
        result = {}
        for pattern, keywords in self.patterns.items():
            result[pattern] = any(keyword in comment for keyword in keywords)
        return result

    def get_missing_patterns(self, current_top30: List[str]) -> List[str]:
        """現在のTOP30で不足しているパターンを特定"""
        pattern_counts = defaultdict(int)

        for comment in current_top30:
            analysis = self.analyze_comment(comment)
            for pattern, found in analysis.items():
                if found:
                    pattern_counts[pattern] += 1

        # 不足パターンを特定（閾値: 2件未満）
        missing = []
        for pattern in self.patterns.keys():
            if pattern_counts[pattern] < 2:
                missing.append(pattern)

        return missing


# 🔍 コメント品質スコアリング
class CommentQualityScorer:
    def __init__(self):
        # 高品質指標
        self.quality_indicators = {
            "具体性": ["具体的", "詳細", "明確", "はっきり", "しっかり"],
            "感情表現": ["気持ち", "快適", "爽やか", "心地", "楽し", "嬉し"],
            "行動提案": ["おすすめ", "注意", "気をつけ", "準備", "対策", "工夫"],
            "時間性": ["朝", "昼", "夕", "夜", "午前", "午後", "明け方", "夕方"],
            "地域性": ["海", "山", "都市", "郊外", "沿岸", "内陸", "平野", "盆地"],
        }

        # 低品質指標（除外対象）
        self.negative_indicators = ["？？？", "不明", "エラー", "###", "NULL", "none"]

    def score_comment(self, comment: str, count: int) -> float:
        """コメントの品質スコアを計算"""
        if any(neg in comment for neg in self.negative_indicators):
            return 0.0

        # 基本スコア（使用回数の対数）
        base_score = min(10.0, count / 1000)

        # 品質ボーナス
        quality_bonus = 0.0
        for category, indicators in self.quality_indicators.items():
            if any(ind in comment for ind in indicators):
                quality_bonus += 1.0

        # 長さボーナス（適度な長さを評価）
        length_bonus = 0.0
        if 4 <= len(comment) <= 12:
            length_bonus = 2.0
        elif 3 <= len(comment) <= 15:
            length_bonus = 1.0

        return base_score + quality_bonus + length_bonus


# 🎯 スマートコメント抽出器
class SmartCommentExtractor:
    def __init__(self):
        self.analyzer = WeatherPatternAnalyzer()
        self.scorer = CommentQualityScorer()

    def extract_enhanced_comments(self, all_comments: List[str], current_top30: List[str], target_count: int = 50) -> List[tuple[str, int, Dict]]:
        """拡張コメントを抽出"""
        # 現在のTOP30を除外
        current_set = set(current_top30)

        # 不足パターンを特定
        missing_patterns = self.analyzer.get_missing_patterns(current_top30)

        # 全コメントのカウント
        comment_counter = Counter(all_comments)

        # 候補コメントを評価
        candidates = []
        for comment, count in comment_counter.items():
            if comment in current_set:
                continue

            # パターン分析
            pattern_analysis = self.analyzer.analyze_comment(comment)

            # 品質スコア計算
            quality_score = self.scorer.score_comment(comment, count)

            # 不足パターンボーナス
            missing_bonus = 0.0
            for pattern in missing_patterns:
                if pattern_analysis.get(pattern, False):
                    missing_bonus += 5.0

            total_score = quality_score + missing_bonus

            candidates.append(
                {
                    "comment": comment,
                    "count": count,
                    "quality_score": quality_score,
                    "missing_bonus": missing_bonus,
                    "total_score": total_score,
                    "patterns": pattern_analysis,
                }
            )

        # スコア順でソート
        candidates.sort(key=lambda x: x["total_score"], reverse=True)

        # 多様性を考慮した選択
        selected = []
        pattern_counts = defaultdict(int)

        for candidate in candidates:
            if len(selected) >= (target_count - 30):
                break

            # パターンバランスをチェック
            dominant_patterns = [p for p, found in candidate["patterns"].items() if found]

            # 同一パターンの過度な集中を避ける
            if dominant_patterns:
                max_pattern_count = max(pattern_counts[p] for p in dominant_patterns) if dominant_patterns else 0
                if max_pattern_count >= 3:  # 同一パターン3件まで
                    continue

            selected.append(candidate)
            for pattern in dominant_patterns:
                pattern_counts[pattern] += 1

        return selected


# 📊 分析レポート生成
def generate_analysis_report(category: str, current_top30: List[str], enhanced_candidates: List[Dict], comment_type: str) -> str:
    """分析レポートを生成"""
    analyzer = WeatherPatternAnalyzer()

    # 現在のパターン分析
    current_patterns = defaultdict(int)
    for comment in current_top30:
        analysis = analyzer.analyze_comment(comment)
        for pattern, found in analysis.items():
            if found:
                current_patterns[pattern] += 1

    # 追加コメントのパターン分析
    new_patterns = defaultdict(int)
    for candidate in enhanced_candidates:
        for pattern, found in candidate["patterns"].items():
            if found:
                new_patterns[pattern] += 1

    report = f"""
# {category}の{comment_type}分析レポート

## 現在のTOP30パターン分布
"""
    for pattern, count in sorted(current_patterns.items()):
        report += f"- {pattern}: {count}件\n"

    report += """
## 追加推奨コメント（上位10件）
"""
    for i, candidate in enumerate(enhanced_candidates[:10], 1):
        patterns = [p for p, found in candidate["patterns"].items() if found]
        report += f"{i}. {candidate['comment']} (使用回数: {candidate['count']}, スコア: {candidate['total_score']:.1f})\n"
        report += f"   パターン: {', '.join(patterns)}\n"

    report += """
## 追加後のパターン改善
"""
    for pattern in analyzer.patterns.keys():
        current = current_patterns[pattern]
        new = new_patterns[pattern]
        if new > 0:
            report += f"- {pattern}: {current}件 → {current + new}件 (+{new})\n"

    return report


# 🔄 メイン処理
def main():
    print("🚀 スマートコメント抽出器を開始...")

    # S3からファイル一覧取得
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    jsonl_keys = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".jsonl")]

    # カテゴリごとのコメント集計
    weather_by_category = defaultdict(list)
    advice_by_category = defaultdict(list)

    # 各ファイルを処理
    for key in sorted(jsonl_keys):
        yyyymm = key.split("/")[-1].replace(".jsonl", "")
        category = classify_category(yyyymm)
        print(f"📂 処理中: {key} → カテゴリ: {category}")

        obj = s3.get_object(Bucket=BUCKET, Key=key)
        lines = obj["Body"].read().decode("utf-8").splitlines()
        for line in lines:
            try:
                data = json.loads(line)
                wc = data.get("weather_comment")
                adv = data.get("advice")
                if wc and len(wc.strip()) > 0:
                    weather_by_category[category].append(wc.strip())
                if adv and len(adv.strip()) > 0:
                    advice_by_category[category].append(adv.strip())
            except json.JSONDecodeError:
                continue

    extractor = SmartCommentExtractor()

    # 📈 weather_comment の処理
    print("\n🌤 Weather Comment処理開始...")
    for cat, comments in weather_by_category.items():
        if not comments:
            continue

        # 現在のTOP30
        current_top30_tuples = Counter(comments).most_common(30)
        current_top30 = [comment for comment, count in current_top30_tuples]

        # 拡張コメント抽出
        enhanced_candidates = extractor.extract_enhanced_comments(
            comments,
            current_top30,
            target_count=50,
        )

        # TOP30 CSV出力
        df_top30 = pd.DataFrame(current_top30_tuples, columns=["weather_comment", "count"])
        output_path_30 = f"output/{cat}_weather_comment_top30.csv"
        df_top30.to_csv(output_path_30, index=False)

        # 拡張版CSV出力（TOP30 + 追加20件）
        enhanced_tuples = [(c["comment"], c["count"]) for c in enhanced_candidates[:20]]
        all_enhanced = current_top30_tuples + enhanced_tuples
        df_enhanced = pd.DataFrame(all_enhanced, columns=["weather_comment", "count"])
        output_path_50 = f"output/{cat}_weather_comment_enhanced50.csv"
        df_enhanced.to_csv(output_path_50, index=False)

        # 分析レポート生成
        report = generate_analysis_report(cat, current_top30, enhanced_candidates, "weather_comment")
        with open(f"output/analysis/{cat}_weather_analysis.md", "w", encoding="utf-8") as f:
            f.write(report)

        print(f"✅ {cat}: TOP30={output_path_30}, Enhanced50={output_path_50}")

    # 📈 advice の処理
    print("\n💡 Advice処理開始...")
    for cat, advices in advice_by_category.items():
        if not advices:
            continue

        # 現在のTOP30
        current_top30_tuples = Counter(advices).most_common(30)
        current_top30 = [advice for advice, count in current_top30_tuples]

        # 拡張コメント抽出
        enhanced_candidates = extractor.extract_enhanced_comments(
            advices,
            current_top30,
            target_count=50,
        )

        # TOP30 CSV出力
        df_top30 = pd.DataFrame(current_top30_tuples, columns=["advice", "count"])
        output_path_30 = f"output/{cat}_advice_top30.csv"
        df_top30.to_csv(output_path_30, index=False)

        # 拡張版CSV出力
        enhanced_tuples = [(c["comment"], c["count"]) for c in enhanced_candidates[:20]]
        all_enhanced = current_top30_tuples + enhanced_tuples
        df_enhanced = pd.DataFrame(all_enhanced, columns=["advice", "count"])
        output_path_50 = f"output/{cat}_advice_enhanced50.csv"
        df_enhanced.to_csv(output_path_50, index=False)

        # 分析レポート生成
        report = generate_analysis_report(cat, current_top30, enhanced_candidates, "advice")
        with open(f"output/analysis/{cat}_advice_analysis.md", "w", encoding="utf-8") as f:
            f.write(report)

        print(f"✅ {cat}: TOP30={output_path_30}, Enhanced50={output_path_50}")

    print("\n🎉 スマートコメント抽出完了！")
    print("📊 分析レポートは output/analysis/ フォルダを確認してください")


if __name__ == "__main__":
    main()
