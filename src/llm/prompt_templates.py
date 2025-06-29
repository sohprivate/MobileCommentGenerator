"""プロンプトテンプレート定義"""

# コメント生成用プロンプトテンプレート
COMMENT_GENERATION_PROMPT = """あなたは天気予報のコメント作成者です。以下の条件でコメントを生成してください。

【現在の天気情報】
- 地点: {location}
- 天気: {weather_condition}
- 気温: {temperature}°C
- 時間帯: {time_period}

【参考コメント】
過去の類似条件でのコメント:
- 天気コメント: "{weather_comment}"
- アドバイス: "{advice_comment}"

【制約条件】
- 必ず{max_length}文字以内
- 自然で親しみやすい表現
- NGワード: {ng_words}
- 季節感を考慮
- 。や、などの句読点は使用せず、スペースや改行も含めない

【良いコメント例】
- "今日は爽やかですね"（9文字）
- "傘をお忘れなく"（7文字）
- "暖かい一日です"（7文字）
- "風が強いです"（6文字）
- "お出かけ日和"（6文字）

【NGコメント例】
- "今日は本当に素晴らしい天気ですね"（16文字 - 長すぎる）
- "危険な暑さです"（7文字 - NGワード使用）
- "絶対に傘を持って"（8文字 - NGワード使用）

コメントを1つだけ生成してください。余計な説明は不要です:"""

# 評価用プロンプトテンプレート（将来使用）
COMMENT_EVALUATION_PROMPT = """以下のコメントを評価してください。

コメント: "{comment}"

評価基準:
1. 文字数が{max_length}文字以内か
2. NGワード（{ng_words}）を含んでいないか
3. 天気情報と整合性があるか
4. 自然で親しみやすい表現か

各項目について「OK」または「NG」で評価し、総合評価を出してください。"""

# エクスポート
__all__ = ["COMMENT_GENERATION_PROMPT", "COMMENT_EVALUATION_PROMPT"]
