# 天気予報コメント生成システム ☀️

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地域の天気情報と過去のコメントデータをもとに、LLM（大規模言語モデル）を利用して短い天気コメント（約15文字）を自動生成します。

## 🆕 最新アップデート (2025-06-15)

- **LLM選択機能の大幅改善**: LLMがコメント選択時の引数不整合を修正
- **タイムゾーン問題の修正**: 時系列データ取得時のdatetime混在エラーを解決
- **予報データ関連の最適化**: 3-6時間間隔での効率的な天気変化追跡
- **プロンプト最適化**: LLMが確実に数値のみを返すよう改善
- **システム改良**: エラーハンドリング強化とパフォーマンス向上

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## 📗 プロジェクト構成

```
MobileCommentGenerator/
├── src/                          # バックエンドPythonアプリケーション
│   ├── data/                     # データクラス・管理
│   │   ├── comment_generation_state.py  # ワークフロー状態管理
│   │   ├── comment_pair.py       # コメントペアデータモデル
│   │   ├── evaluation_criteria.py       # 評価基準定義
│   │   ├── forecast_cache.py     # 天気予報キャッシュ管理
│   │   ├── location_manager.py   # 地域データ管理
│   │   ├── past_comment.py       # 過去コメント管理
│   │   ├── weather_data.py       # 天気データモデル
│   │   ├── weather_trend.py      # 天気傾向分析
│   │   └── Chiten.csv            # 地域マスターデータ
│   ├── apis/                     # 外部API連携
│   │   └── wxtech_client.py      # WxTech天気API統合
│   ├── algorithms/               # アルゴリズム実装
│   │   ├── comment_evaluator.py        # コメント評価ロジック
│   │   └── similarity_calculator.py    # 類似度計算
│   ├── nodes/                    # LangGraphノード
│   │   ├── input_node.py         # 入力ノード
│   │   ├── weather_forecast_node.py     # 天気予報取得ノード
│   │   ├── retrieve_past_comments_node.py # 過去コメント取得ノード
│   │   ├── select_comment_pair_node.py  # コメント選択ノード
│   │   ├── comment_selector.py   # コメント選択ロジック
│   │   ├── evaluate_candidate_node.py   # 候補評価ノード
│   │   ├── generate_comment_node.py     # コメント生成ノード
│   │   ├── output_node.py        # 出力ノード
│   │   └── mock_nodes.py         # モックノード（テスト用）
│   ├── workflows/                # ワークフロー実装
│   │   └── comment_generation_workflow.py
│   ├── llm/                      # LLM統合
│   │   ├── llm_client.py         # LLMクライアント基底
│   │   ├── llm_manager.py        # LLMマネージャー
│   │   ├── prompt_builder.py     # プロンプト構築
│   │   ├── prompt_templates.py   # プロンプトテンプレート
│   │   └── providers/            # LLMプロバイダー実装
│   │       ├── base_provider.py         # 基底プロバイダー
│   │       ├── openai_provider.py       # OpenAI統合
│   │       ├── gemini_provider.py       # Google Gemini統合
│   │       └── anthropic_provider.py    # Anthropic Claude統合
│   ├── repositories/             # データリポジトリ
│   │   ├── local_comment_repository.py # ローカルデータアクセス
│   │   └── s3_comment_repository.py     # S3データアクセス
│   ├── utils/                    # ユーティリティ
│   │   ├── common_utils.py       # 共通ユーティリティ
│   │   └── weather_comment_validator.py # 天気コメント検証
│   ├── ui/                       # Streamlit UI
│   │   ├── streamlit_components.py      # UIコンポーネント
│   │   ├── streamlit_utils.py    # UIユーティリティ
│   │   └── pages/                # マルチページ構成
│   │       └── statistics.py     # 統計情報ページ
│   └── config/                   # 設定管理
│       ├── weather_config.py     # 天気予報設定
│       ├── comment_config.py     # コメント生成設定
│       ├── config_loader.py      # 設定ローダー
│       └── severe_weather_config.py # 悪天候設定
├── frontend/                     # Vue.js/Nuxt.jsフロントエンド（完全分離）
│   ├── pages/                    # ページコンポーネント
│   │   └── index.vue             # メインページ（全体レイアウト・状態管理）
│   ├── components/               # UIコンポーネント
│   │   ├── LocationSelection.vue    # 地域選択（地区別リスト・検索機能）
│   │   ├── GenerateSettings.vue     # 生成設定（LLMプロバイダー選択）
│   │   ├── GeneratedComment.vue     # 生成結果表示（コメント・履歴）
│   │   └── WeatherData.vue          # 天気データ表示（予報情報・詳細）
│   ├── composables/              # Composition API
│   │   └── useApi.ts             # API呼び出し（REST通信・エラーハンドリング）
│   ├── constants/                # 定数定義
│   │   ├── locations.ts          # 地域データ（全国地域リスト）
│   │   └── regions.ts            # 地区データ（地区分類・表示順）
│   ├── types/                    # TypeScript型定義
│   │   └── index.ts              # API・UI内の型定義
│   ├── app.vue                   # アプリケーション全体のレイアウト
│   ├── nuxt.config.ts            # Nuxt設定（UIモジュール設定）
│   ├── package.json              # Node.js依存関係
│   └── start_frontend.sh         # フロントエンド起動スクリプト
├── api_server.py                 # FastAPI APIサーバー
├── app.py                        # Streamlitメインエントリポイント
├── start_api.sh                  # APIサーバー起動スクリプト
├── data/                         # データファイル
│   ├── forecast_cache/           # 天気予報キャッシュ
│   └── generation_history.json  # 生成履歴
├── config/                       # 設定ファイル（YAML）
│   ├── weather_thresholds.yaml   # 天気閾値設定
│   ├── expression_rules.yaml     # 表現ルール
│   ├── ng_words.yaml             # NGワード
│   └── llm_config.yaml           # LLM設定
├── output/                       # 生成されたCSVファイル・分析結果
├── tests/                        # テストスイート
│   ├── integration/              # 統合テスト
│   └── test_*.py                 # 各種ユニットテスト
├── docs/                         # ドキュメント
├── scripts/                      # ユーティリティスクリプト
├── examples/                     # サンプルコード
├── pyproject.toml                # プロジェクト設定・依存関係
├── uv.lock                       # uvロックファイル
├── requirements.txt              # 従来の依存関係ファイル
├── pytest.ini                    # pytest設定
├── mypy.ini                      # mypy設定
├── Makefile                      # ビルド・実行スクリプト
├── setup.sh                     # セットアップスクリプト
└── README.md                     # このファイル
```

## 🎯 主な特徴

- **LangGraphワークフロー**: 状態とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic対応  
- **適応性ベース選択**: 過去コメントから最適なペアを適応性でLLM選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **12時間後天気予報**: デフォルトで12時間後のデータを使用
- **デュアルUI実装**: Streamlit（開発用）+ Vue.js/Nuxt.js（本番用）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能

## 📊 現在の進捗状況

### ✅ Phase 1: 基盤システム（100%完了）
- [x] **地域データ管理システム**: CSV読み込み検証・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合（12時間後データ対応）
- [x] **過去コメント取得**: enhanced50.csvベースのデータ解析・類似度選択検証
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント類似度選択ベースによる選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの順次実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト実装
- [x] **ワークフロー可視化**: 実装トレースツール

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基本UI実装**: 地域選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 天気情報・過去コメント・評価結果詳細表示
- [x] **バッチ処理**: 複数地域一括処理機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### ✅ Phase 4: フロントエンド分離（100%完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト構造の明確化**: frontend/とsrc/の責任分離
- [x] **API実装**: FastAPI RESTful APIエンドポイント完成
- [x] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド
- [x] **UIコンポーネント**: 地域選択・設定・結果表示の完全実装

### 🚀 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 📄 セットアップ

### 環境要件
- Python 3.10以上
- uv（推奨）
- Node.js 18以上（フロントエンド用）

### クイックスタート (uv使用)

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. 依存関係インストール（uvが自動的に仮想環境作成）
uv sync

# 3. 環境変数設定
cp .env.example .env
# .envファイルでAPIキーを設定

# 4. アプリケーション起動
# バックエンド（FastAPI）
uv run ./start_api.sh

# フロントエンド（別ターミナル）
cd frontend
npm install
npm run dev
```

アクセスURL:
- フロントエンド: http://localhost:3000
- API: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs

### 代替セットアップ方法

#### Streamlit版（開発・デバッグ用）

```bash
# 仮想環境がすべて作成されている場合
uv run streamlit run app.py
```

#### その他のスクリプト

```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev

# Makefile使用
make setup
make help
```

## 🔑 API キー設定

### 必要設定
`.env`ファイルでLLMプロバイダーのAPIキーを設定:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 天気予報データ
WXTECH_API_KEY=your_wxtech_api_key_here

# AWS（オプション）
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## 🌤️ 天気予報時刻の設定

システムは**翌日9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。具体的には9:00, 12:00, 15:00, 18:00の4つの時刻の予報を取得し、天気の優先順位に従って最適な予報を選択します。

### 天気の優先順位ルール

1. **特殊気象条件最優先**: 雷、霧、嵐など
2. **本降りの雨(>10mm/h)**: 猛暑日でも優先  
3. **猛暑日(35℃以上)**: 雨が少数（≤50%）なら熱中症対策を優先、雨が多数（>50%）なら雨を優先
4. **悪天候**: 降水量の多い順
5. **雨天**: 降水量の多い順  
6. **曇り**: 晴れ以外の条件を優先
7. **晴れ**: 最高気温の時間帯を選択

### 予報選択の例

- **晴れ3回、雨1回** → 雨を選択（「折り畳み傘」等のコメント）
- **晴れ1回、小雨2回、大雨1回** → 大雨を選択（「念のため備えて」等のコメント）  
- **猛暑日35℃以上+小雨1回** → 最高気温を選択（熱中症対策優先）
- **猛暑日35℃以上+雨3回** → 最大降水量を選択（雨優先）

### 設定の確認

選択された天気データは、UIの各地域詳細情報で「🕐 予報時刻」として表示されます。表示される時刻は日本標準時（JST）です。

**注意**: この設定により、すべてのコンポーネントで翌日の9時間帯から選択された天気データが統一的に使用されます。

## 📄 フロントエンド詳細

### ファイル構成と役割

| ファイル | 役割 | 主な機能 |
|---------|------|----------|
| **pages/index.vue** | メインページ | 全体レイアウト・状態管理・ページ全体の制御 |
| **app.vue** | アプリケーションルート | グローバルスタイル・共通レイアウト |
| **components/LocationSelection.vue** | 地域選択コンポーネント | 地区別地域リスト・検索・フィルタリング機能 |
| **components/GenerateSettings.vue** | 設定コンポーネント | LLMプロバイダー選択・生成オプション設定 |
| **components/GeneratedComment.vue** | 結果表示コンポーネント | 生成コメント表示・履歴・コピー機能 |
| **components/WeatherData.vue** | 天気情報コンポーネント | 現在・予報天気データ・詳細情報表示 |
| **composables/useApi.ts** | API通信層 | REST API呼び出し・エラーハンドリング・ローディング状態 |
| **constants/locations.ts** | 地域データ | 全国地域の座標・名称・地区分類 |
| **constants/regions.ts** | 地区データ | 地区分類表示順・カテゴリ分類 |
| **types/index.ts** | 型定義 | TypeScript型・API仕様・UI状態の型定義 |

### 状態管理

```typescript
// pages/index.vueでの主要状態
const selectedLocation = ref<Location | null>(null)
const generatedComment = ref<GeneratedComment | null>(null)
const isGenerating = ref(false)
const error = ref<string | null>(null)
```

### API通信

```typescript
// composables/useApi.ts
export const useApi = () => {
  // 地域一覧取得
  const getLocations = async (): Promise<Location[]>
  
  // コメント生成
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // 生成履歴取得
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### UI機能詳細

#### LocationSelection.vue
- **地区フィルタ**: 北海道・東北・関東などの地区別表示・検索機能
- **検索機能**: 地域名による絞り込み・フィルタリング
- **お気に入り**: よく使う地域の保存・優先表示
- **レスポンシブ**: モバイル・タブレット対応

#### GenerateSettings.vue
- **LLMプロバイダー選択**: OpenAI・Gemini・Anthropic
- **APIキー状態表示**: 設定済みプロバイダーのアイコン表示
- **生成オプション**: 詳細設定（将来の拡張用）

#### GeneratedComment.vue
- **コメント表示**: 天気コメント・アドバイス一体表示
- **コピー機能**: ワンクリックでクリップボードにコピー
- **生成履歴**: 過去の生成結果一覧・時系列表示
- **エクスポート**: CSV形式でのダウンロード機能

#### WeatherData.vue
- **現在天気**: リアルタイム天気情報
- **12時間予報**: デフォルト予報時刻の詳細表示・気温傾向表示
- **気象パラメータ**: 風速・湿度・降水量など詳細情報
- **警告情報**: 悪天候時の注意喚起表示

## 🚀 使用方法

### Vue.jsフロントエンド（推奨）

```bash
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 左パネルから地域と天気を地域を選択
3. LLMプロバイダーを選択
4. 「コメント生成」ボタンをクリック
5. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルから地域とLLMプロバイダーを選択
3. 「🎯 コメント生成」ボタンをクリック
4. 生成されたコメントと詳細情報を確認

### プログラマティック使用

```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# 単一地域のコメント生成
result = run_comment_generation(
    location_name="東京",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"生成コメント: {result['final_comment']}")
```

## 🧪 テスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration

# クイックテスト（主要機能のみ）
make quick-test
```

## 🔧 開発ツール

### コード品質

```bash
# コード品質チェック
make lint                         # コード品質チェック
make format                       # コードフォーマット
make type-check                   # 型チェック
```

### 設定済みツール
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

### その他便利なコマンド

```bash
# メンテナンス
make clean                        # 一時ファイル削除
uv sync                           # 依存関係更新

# ログ出力
tail -f logs/llm_generation.log    # LLMジェネレーションログ

# ヘルプ
make help
```

## 📊 プロジェクト情報

### 技術スタック

**バックエンド:**
- Python 3.10+
- LangGraph 0.0.35+
- LangChain 0.1.0+
- Streamlit 1.28.0+
- OpenAI/Gemini/Anthropic APIs

**フロントエンド:**
- Vue.js 3.5+
- Nuxt.js 3.17+
- TypeScript 5.3+
- FastAPI 0.104+

**データ処理:**
- Pandas 2.1.4+
- NumPy 1.26.2+
- Scikit-learn 1.3.2+

**AWS (オプション):**
- Boto3 1.34.0+
- AWS CLI 1.32.0+

### メタデータ
- **バージョン**: 1.0.0
- **ライセンス**: MIT
- **最終更新**: 2025-06-15
- **開発チーム**: WNI Team

## 📝 更新履歴

- **v1.1.1** (2025-06-15): LLM選択機能とタイムゾーン問題修正・プロンプト最適化
- **v1.1.0** (2025-06-15): FastAPI統合・フロントエンド分離完了・PastComment修正
- **v1.0.0** (2025-06-12): Phase 4完了 - Vue.js/Nuxt.jsフロントエンド実装
- **v0.3.0** (2025-06-06): Phase 2完了 - LangGraphワークフロー実装

### 🐛 修正内容 (v1.1.1)

**LLM選択機能の修正:**
- `comment_selector.py`: LLMAPI呼び出し時の引数不整合を修正
- プロンプト改善で確実な数値選択を実現
- 天気・アドバイス一体コメントでLLM選択が正常動作

**タイムゾーン問題の修正:**
- timezone-aware/naive datetime混在エラーを解決
- 時系列データ取得の安定性向上
- 予報データ間隔: 3-6時間間隔での効率的な天気変化追跡

**システム改善:**
- エラーハンドリングの強化
- 予報データの堅牢性向上
- プロンプト最適化でLLMレスポンス精度向上

**動作確認済み:**
- 天気コメント: LLMによる適切な選択
- アドバイスコメント: 34番「お出かけＯＫ」選択成功
- 最終出力: 「昼間は穏やか　お出かけＯＫ」生成確認

🚀 生成されたコメントが地域・天気条件に応じて適切に変化することを確認

## 🤝 コントリビューション

1. Issue作成で問題報告・機能要望
2. Fork & Pull Requestでの貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 🔗 サポート

問題が解決しない場合は、GitHubのIssuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**