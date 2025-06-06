# 天気コメント生成システム

LangGraphとLLMを活用した天気コメント自動生成システムです。

## 現在の実装状況

### ✅ Phase 1: 基盤機能（完了）

#### ✅ 地点データ管理システム (Issue #2) - **完了**
地点データの読み込み、検索、正規化機能が実装されています。
- `src/data/location_manager.py`: 包括的な地点管理機能
- 47都道府県・8地方区分の自動推定
- 高性能検索エンジン（レーベンシュタイン距離によるあいまい検索）
- 距離計算機能（ハヴァーサイン式）

#### ✅ 天気予報統合機能 (Issue #3) - **完了**
Weathernews WxTech APIとの統合が完了しています。
- `src/apis/wxtech_client.py`: APIクライアント実装
- `src/nodes/weather_forecast_node.py`: LangGraphノード実装
- 同期・非同期両対応
- リトライ機能とエラーハンドリング

#### ✅ S3過去コメント取得機能 (Issue #4) - **完了**
S3バケットからの過去コメント取得と類似検索が実装されています。
- `src/repositories/s3_comment_repository.py`: S3連携
- `src/nodes/retrieve_past_comments_node.py`: LangGraphノード
- 類似度計算アルゴリズム実装
- コメントタイプ（weather_comment/advice）の管理

### 🔄 Phase 2: LangGraphワークフロー統合（実装中）

#### ✅ LLM統合とGenerateCommentNode (Issue #8) - **完了**
マルチLLMプロバイダー対応のコメント生成機能が実装されています。
- OpenAI、Gemini、Anthropic Claude対応
- 15文字制限の遵守
- プロンプトエンジニアリング実装

#### 🚧 コメント選択・類似度計算 (Issue #5) - **実装予定**
- コサイン類似度による過去コメントペア選択
- 天気条件・セマンティック類似度の総合評価

#### 🚧 コメント評価・バリデーション (Issue #6) - **実装予定**
- 15文字制限チェック
- NG表現・不適切ワードの検出
- 表現ルールの適用

#### 🚧 LangGraphワークフロー統合 (Issue #7) - **優先実装中**
全ノードを統合したエンドツーエンドのワークフロー構築
```
InputNode → FetchForecastNode → RetrievePastCommentsNode
    ↓
SelectCommentPair → EvaluateCandidate → GenerateComment → OutputNode
    ↑_______________|（リトライループ）
```

### 📋 Phase 3: UI・フロントエンド（計画中）

#### 📋 Streamlitバックエンド (Issue #9)
#### 📋 React/TypeScriptフロントエンド (Issue #10)

### 📋 Phase 4: デプロイメント（計画中）

#### 📋 AWSデプロイメント (Issue #11)

## システムの主な処理フロー

1. **地点読み込み**: `Chiten.csv` を読み取り、地点名と緯度経度を取得
2. **天気予報取得**: WxTech API から 12h／24h 先の予報を取得
3. **過去コメント取得**: S3 から対象年月の JSONL を読み込み、地点名でフィルタ
4. **コメント候補選定**: 予報条件に近い `weather_comment` / `advice` ペアを抽出
5. **LLM 生成**: 選定したペアをプロンプトに組み込み、LLM に新規コメント生成を依頼
6. **ルールチェック**: 表現ルールを自動検証し、問題があれば再生成または別ペアを選択
7. **結果表示**: フロントエンドにコメントを返却し、ユーザーはコピー可能

## 環境構築

### 前提条件

* Python 3.10 以上
* AWS CLI (S3 連携用)
* OpenAI, Anthropic, Gemini, WxTech の API キー

### バックエンドセットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 環境変数を設定
```

### 必要な環境変数

```env
# Weather API
WXTECH_API_KEY=your_wxtech_api_key

# LLM Providers
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-northeast-1
```

## 使用方法

現在、個別機能のテストが可能です。完全なワークフローはIssue #7の完了後に利用可能になります。

### 地点検索の例
```python
from src.data.location_manager import LocationManager

manager = LocationManager("Chiten.csv")
results = manager.search_location("東京")
```

### 天気予報取得の例
```python
from src.apis.wxtech_client import WxTechAPIClient

client = WxTechAPIClient(api_key)
forecast = client.get_forecast(35.6762, 139.6503)  # 東京
```

### 過去コメント取得の例
```python
from src.repositories.s3_comment_repository import S3CommentRepository

repo = S3CommentRepository()
comments = repo.fetch_comments_by_period('202406')
```

## テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=src --cov-report=html

# 特定のテストファイル実行
pytest tests/test_location_manager.py
```

## プロジェクト構造

```
.
├── src/
│   ├── data/                # データクラス・管理
│   │   ├── location_manager.py     # 地点管理 ✅
│   │   ├── weather_data.py         # 天気データ ✅
│   │   ├── past_comment.py         # 過去コメント ✅
│   │   └── comment_generation_state.py  # LangGraph状態管理 ✅
│   ├── apis/                # 外部API連携
│   │   └── wxtech_client.py        # WxTech API ✅
│   ├── repositories/        # データリポジトリ
│   │   └── s3_comment_repository.py # S3連携 ✅
│   ├── nodes/              # LangGraphノード
│   │   ├── weather_forecast_node.py     # 天気予報取得 ✅
│   │   ├── retrieve_past_comments_node.py # 過去コメント取得 ✅
│   │   ├── generate_comment_node.py      # コメント生成 ✅
│   │   ├── select_comment_pair_node.py   # コメント選択 🚧
│   │   └── evaluate_candidate_node.py    # 評価・検証 🚧
│   ├── llm/                # LLM統合
│   │   ├── llm_client.py           # マルチLLMクライアント ✅
│   │   └── prompt_builder.py       # プロンプト構築 ✅
│   └── config/             # 設定管理
│       ├── weather_config.py       # 天気API設定 ✅
│       └── llm_config.py          # LLM設定 ✅
├── tests/                  # テストスイート
├── docs/                   # ドキュメント
├── examples/               # 使用例
├── Chiten.csv             # 地点データ
├── requirements.txt        # 依存関係
└── README.md              # このファイル
```

## 今後の開発予定

### 直近の優先事項（Issue #17）
1. **LangGraphワークフロー骨格の実装**
   - モックノードを使用した基本フローの確立
   - エンドツーエンドテストの実装
   
2. **表現ルール設定の具体化**
   - NGワード設定ファイルの作成
   - バリデーションルールの実装

3. **ノード統合の段階的実施**
   - 実装済みノードから順次統合
   - モックノードの実装置き換え

## 貢献方法

1. 各Issueの受け入れ条件を確認
2. 実装前にテストを書く（TDD推奨）
3. 型ヒントとdocstringを必ず記述
4. テストカバレッジ80%以上を維持

## ライセンス

MIT License

---

**Current Status**: Phase 2 実装中 🚧  
**Next Milestone**: Issue #7 (LangGraphワークフロー統合)
