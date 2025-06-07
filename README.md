# 天気予報コメント生成プロジェクト

LangGraphとLLMを活用した天気コメント自動生成システムです。

## 🌟 プロジェクト概要

本プロジェクトは、Python/StreamlitバックエンドとVue.js/TypeScriptフロントエンドから構成される天気予報コメント生成システムです。指定した各地点の天気予報データと過去のコメントデータをもとに、LLM（大規模言語モデル）を活用して短い天気コメント（約15文字）を自動生成します。

### 主な特徴
- **LangGraphワークフロー**: 状態遷移と再試行ロジックを洗練に記述
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応
- **類似度ベース選択**: 過去コメントから最適なペアを選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **リアルタイムUI**: Streamlit/Vue.jsによる直感的な操作

## 📊 現在の進捗状況（2025/6/7時点）

### ✅ Phase 1: 基盤機能（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・検索・正規化機能
- [x] **天気予報統合機能**: WxTech API統合
- [x] **S3過去コメント取得**: JSONL解析・類似検索
- [x] **LLM統合**: マルチプロバイダー対応

### 🚧 Phase 2: LangGraphワークフロー（90%完了）
- [x] **SelectCommentPairNode**: コサイン類似度による選択 ✨ NEW
- [x] **EvaluateCandidateNode**: 8つの評価基準による検証 ✨ NEW
- [x] **基本ワークフロー**: 実装版ノードでの骨格実装 ✨ NEW
- [x] **InputNode/OutputNode**: 本実装完了 ✨ NEW
- [ ] **統合テスト**: エンドツーエンドテスト実施中

### 📱 Phase 3: UI実装（100%完了）
- [x] **Streamlit UI**: Web UIの実装
- [x] **Vue.js/TypeScript**: モダンなフロントエンド

### 🚀 Phase 4: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🔄 システムの主な処理フロー

```
┌─────────────┐      ┌──────────────────┐      ┌────────────────────────┐
│ InputNode   │──▶──│ FetchForecastNode │──▶──│ RetrievePastCommentsNode │
└─────────────┘      └──────────────────┘      └────────────────────────┘
                                                            │
      ┌─────────────────────────────────────────────────────┘
      ▼
      ┌──────────────────┐
      │ SelectCommentPair │ ✨ 実装完了
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐  Failure  ┌──────────────────┐
      │ EvaluateCandidate│ ────────▶ │ SelectCommentPair │
      └──────────────────┘           └──────────────────┘
                │ Success                (リトライループ)
                ▼
      ┌──────────────────┐
      │ GenerateComment   │
      └──────────────────┘
                │
                ▼
      ┌──────────────────┐
      │ OutputNode       │
      └──────────────────┘
```

## 🛠️ 技術スタック

### バックエンド
- **Python 3.10+**
- **LangGraph**: ワークフロー管理
- **Streamlit**: Web UI
- **boto3**: AWS S3連携
- **requests/aiohttp**: API通信

### フロントエンド
- **Vue.js 3/Nuxt 3**
- **TypeScript**
- **Composition API**
- **Scoped CSS**

### LLMプロバイダー
- **OpenAI API**
- **Google Gemini API**
- **Anthropic Claude API**

### データソース
- **Weathernews WxTech API**: 12h/24h予報
- **S3バケット**: 過去コメントJSONL
- **地点リストCSV**: Chiten.csv

## 🚀 セットアップ

### 前提条件
- Python 3.10以上
- Node.js 18以上
- AWS CLI（S3連携用）
- 各種APIキー

### バックエンドセットアップ
```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# Streamlit起動
streamlit run app.py
```

### フロントエンドセットアップ
```bash
cd src/tool_design
npm install
npm run dev
```

## 📊 主要機能

### 1. 地点管理
```python
from src.data.location_manager import LocationManager

manager = LocationManager("Chiten.csv")
results = manager.search_location("東京", fuzzy=True)
```

### 2. 天気予報取得
```python
from src.apis.wxtech_client import WxTechAPIClient

client = WxTechAPIClient(api_key)
forecast = client.get_forecast(35.6762, 139.6503)
```

### 3. 過去コメント検索
```python
from src.repositories.s3_comment_repository import S3CommentRepository

repo = S3CommentRepository()
comments = repo.search_similar_comments(
    target_weather_condition="晴れ",
    target_temperature=25.0,
    target_location="東京"
)
```

### 4. コメント生成
```python
from src.workflows.comment_generation_workflow import run_comment_generation

result = run_comment_generation(
    location_name="東京",
    llm_provider="openai"
)
print(result['final_comment'])
```

## 🧪 テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=src --cov-report=html

# 特定のテスト実行
pytest tests/test_location_manager.py
```

## 📁 プロジェクト構造

```
.
├── src/
│   ├── data/               # データクラス・管理
│   ├── apis/               # 外部API連携
│   ├── repositories/       # データリポジトリ
│   ├── nodes/              # LangGraphノード
│   ├── workflows/          # ワークフロー定義
│   ├── algorithms/         # 類似度計算等 ✨ NEW
│   ├── llm/                # LLM統合
│   ├── ui/                 # Streamlit UI
│   └── config/             # 設定管理
├── tests/                  # テストスイート
├── docs/                   # ドキュメント
├── examples/               # 使用例
└── src/tool_design/        # Vue.jsフロントエンド
```

## 🔥 最近の更新（2025/6/7）

### 実装完了
1. **SelectCommentPairNode統合**
   - コサイン類似度計算エンジン実装
   - 天気条件・気温・地点・時間帯による類似度計算
   - weather_commentとadviceのペア選択機能

2. **EvaluateCandidateNode統合**
   - 8つの評価基準（関連性、創造性、自然さ、適切性、エンゲージメント、明確性、一貫性、オリジナリティ）
   - 不適切表現の検出機能
   - 合格/不合格判定とリトライメカニズム

3. **ワークフロー更新**
   - モックノードから実装版への完全移行
   - InputNode/OutputNode本実装完了

### 次の優先事項
1. 統合テスト実施
2. 地点データ管理システム実装（Issue #2）
3. パフォーマンス最適化
4. AWSデプロイメント準備

## 🤝 コントリビューション

1. Issueの確認と選択
2. ブランチ作成: `feature/issue-{number}-{description}`
3. テスト作成（TDD推奨）
4. PR作成とレビュー依頼

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## 📝 ライセンス

MIT License

## 👥 開発チーム

- **Project Lead**: @sakamo-wni
- **Contributors**: @ah925

---

**Last Updated**: 2025/06/07  
**Status**: Active Development