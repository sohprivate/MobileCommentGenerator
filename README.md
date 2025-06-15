# 天気予報コメント生成システム ☁️

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地点の天気情報と過去のコメントデータをもとに、LLM（大規模言語モデル）を利用して短い天気コメント（約15文字）を自動生成します。

## 🆕 最新アップデート (2025-06-15)

- **LLM選択機能の大幅改善**: コメント選択でLLMが確実に動作するよう修正
- **タイムゾーン問題の修正**: 時系列データ取得時のdatetime型不整合を解決
- **予報データ間隔の最適化**: 3-6時間間隔での効率的な天気変化追跡
- **プロンプト最適化**: LLMが数値のみを返すよう指示文を改善

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🗂️ プロジェクト構成

```
MobileCommentGenerator/
├── src/                        # バックエンドPythonアプリケーション
│   ├── data/                   # データクラス・管理
│   │   ├── comment_generation_state.py  # ワークフロー状態管理
│   │   ├── comment_pair.py     # コメントペアデータモデル
│   │   ├── evaluation_criteria.py      # 評価基準定義
│   │   ├── forecast_cache.py   # 天気予報キャッシュ管理
│   │   ├── location_manager.py # 地点データ管理
│   │   ├── past_comment.py     # 過去コメント管理
│   │   ├── weather_data.py     # 天気データモデル
│   │   ├── weather_trend.py    # 天気傾向分析
│   │   └── Chiten.csv          # 地点マスターデータ
│   ├── apis/                   # 外部API連携
│   │   └── wxtech_client.py    # WxTech天気API統合
│   ├── algorithms/             # アルゴリズム実装
│   │   ├── comment_evaluator.py        # コメント評価ロジック
│   │   └── similarity_calculator.py    # 類似度計算
│   ├── nodes/                  # LangGraphノード
│   │   ├── input_node.py       # 入力ノード
│   │   ├── weather_forecast_node.py    # 天気予報取得ノード
│   │   ├── retrieve_past_comments_node.py # 過去コメント取得ノード
│   │   ├── select_comment_pair_node.py  # コメント選択ノード
│   │   ├── comment_selector.py # コメント選択ロジック
│   │   ├── evaluate_candidate_node.py   # 候補評価ノード
│   │   ├── generate_comment_node.py     # コメント生成ノード
│   │   ├── output_node.py      # 出力ノード
│   │   └── mock_nodes.py       # モックノード（テスト用）
│   ├── workflows/              # ワークフロー実装
│   │   └── comment_generation_workflow.py
│   ├── llm/                    # LLM統合
│   │   ├── llm_client.py       # LLMクライアント基底
│   │   ├── llm_manager.py      # LLMマネージャー
│   │   ├── prompt_builder.py   # プロンプト構築
│   │   ├── prompt_templates.py # プロンプトテンプレート
│   │   └── providers/          # LLMプロバイダー実装
│   │       ├── base_provider.py        # 基底プロバイダー
│   │       ├── openai_provider.py      # OpenAI統合
│   │       ├── gemini_provider.py      # Google Gemini統合
│   │       └── anthropic_provider.py   # Anthropic Claude統合
│   ├── repositories/           # データリポジトリ
│   │   ├── local_comment_repository.py # ローカルデータアクセス
│   │   └── s3_comment_repository.py    # S3データアクセス
│   ├── utils/                  # ユーティリティ
│   │   ├── common_utils.py     # 共通ユーティリティ
│   │   └── weather_comment_validator.py # 天気コメント検証
│   ├── ui/                     # Streamlit UI
│   │   ├── streamlit_components.py     # UIコンポーネント
│   │   ├── streamlit_utils.py  # UIユーティリティ
│   │   └── pages/              # マルチページ構成
│   │       └── statistics.py   # 統計情報ページ
│   └── config/                 # 設定管理
│       ├── weather_config.py   # 天気予報設定
│       ├── comment_config.py   # コメント生成設定
│       ├── config_loader.py    # 設定ローダー
│       └── severe_weather_config.py # 悪天候設定
├── frontend/                   # Vue.js/Nuxt.jsフロントエンド（完全分離）
│   ├── pages/                  # ページコンポーネント
│   │   └── index.vue           # メインページ（全体レイアウト・状態管理）
│   ├── components/             # UIコンポーネント
│   │   ├── LocationSelection.vue    # 地点選択（地域別リスト・検索機能）
│   │   ├── GenerateSettings.vue     # 生成設定（LLMプロバイダー選択）
│   │   ├── GeneratedComment.vue     # 生成結果表示（コメント・履歴）
│   │   └── WeatherData.vue          # 天気データ表示（予報情報・詳細）
│   ├── composables/            # Composition API
│   │   └── useApi.ts           # API呼び出し（REST通信・エラーハンドリング）
│   ├── constants/              # 定数定義
│   │   ├── locations.ts        # 地点データ（全国地点リスト）
│   │   └── regions.ts          # 地域データ（地域分類・表示順）
│   ├── types/                  # TypeScript型定義
│   │   └── index.ts           # API・UIの型定義
│   ├── app.vue                 # アプリ全体のレイアウト
│   ├── nuxt.config.ts          # Nuxt設定（UI・モジュール設定）
│   ├── package.json            # Node.js依存関係
│   └── start_frontend.sh       # フロントエンド起動スクリプト
├── api_server.py               # FastAPI APIサーバー
├── app.py                      # Streamlitメインエントリポイント
├── start_api.sh                # APIサーバー起動スクリプト
├── data/                       # データファイル
│   ├── forecast_cache/         # 天気予報キャッシュ
│   └── generation_history.json # 生成履歴
├── config/                     # 設定ファイル（YAML）
│   ├── weather_thresholds.yaml # 天気閾値設定
│   ├── expression_rules.yaml   # 表現ルール
│   ├── ng_words.yaml           # NGワード
│   └── llm_config.yaml         # LLM設定
├── output/                     # 生成されたCSVファイル・分析結果
├── tests/                      # テストスイート
│   ├── integration/            # 統合テスト
│   └── test_*.py               # 各種ユニットテスト
├── docs/                       # ドキュメント
├── scripts/                    # ユーティリティスクリプト
├── examples/                   # サンプルコード
├── pyproject.toml              # プロジェクト設定・依存関係
├── uv.lock                     # uvロックファイル
├── requirements*.txt           # 従来の依存関係ファイル
├── pytest.ini                 # pytest設定
├── mypy.ini                    # mypy設定
├── Makefile                    # ビルド・実行スクリプト
├── setup.sh                    # セットアップスクリプト
└── README.md                   # このファイル
```

## 🌟 主な特徴

- **LangGraphワークフロー**: 状態とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応  
- **適応性ベース選択**: 過去コメントから最適なペアを選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **12時間後天気予報**: デフォルトで12時間後の天気データを使用
- **デュアルUI実装**: Streamlit（開発用）+ Vue.js/Nuxt.js（本番用）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能

## 📊 現在の進捗状況

### ✅ Phase 1: 基礎機能（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・更新検証・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合（12時間後データ対応）
- [x] **過去コメント取得**: enhanced50.csvベースのデータ解析・頻度選択検証
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント頻度選択ベースによる選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの骨格実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト実装
- [x] **ワークフロー可視化**: 実行トレース記録ツール

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基本UI実装**: 地点選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 天気情報・過去コメント・評価結果表示
- [x] **バッチ処理**: 複数地点一括処理機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### ✅ Phase 4: フロントエンド分離（100%完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト構造の明確化**: frontend/とsrc/の責任分離
- [x] **API実装**: FastAPI RESTful APIエンドポイント完成
- [x] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド
- [x] **UIコンポーネント**: 地点選択・設定・結果表示の完全実装

### 🚀 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🔧 セットアップ

### 環境要件
- Python 3.10以上
- uv（推奨）
- Node.js 18以上（フロントエンド用）

### クイックスタート (uv使用)

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. 依存関係インストール（uvが自動的に仮想環境を作成）
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
# 仮想環境がすでに作成されている場合
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

### 必須設定
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

## ⚙️ 天気予報時刻の設定

システムはデフォルトで**12時間後の天気予報データ**を使用してコメントを生成します。この設定は環境変数で簡単に変更できます。

### 環境変数での設定

`.env`ファイルに以下の環境変数を追加してください：

```bash
# 何時間後の予報を使用するか（デフォルト: 12）
WEATHER_FORECAST_HOURS_AHEAD=12
```

### 設定例

```bash
# 6時間後の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=6

# 24時間後（翌日同時刻）の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=24

# 3時間後の予報を使用する場合
WEATHER_FORECAST_HOURS_AHEAD=3
```

### 設定の確認

設定した時刻は、UIの各地点詳細情報で「⏰ 予報時刻」として表示されます。表示される時刻は日本標準時（JST）に自動変換されます。

**注意**: この設定により、すべてのコンポーネントで統一的に指定した時間後の予報が使用されます。

## 🎨 フロントエンド詳細

### 📁 ファイル構成と役割

| ファイル | 役割 | 主な機能 |
|---------|------|----------|
| **pages/index.vue** | メインページ | 全体レイアウト・状態管理・ページ全体の制御 |
| **app.vue** | アプリケーションルート | グローバルスタイル・共通レイアウト |
| **components/LocationSelection.vue** | 地点選択コンポーネント | 地域別地点リスト・検索・フィルタリング機能 |
| **components/GenerateSettings.vue** | 設定コンポーネント | LLMプロバイダー選択・生成オプション設定 |
| **components/GeneratedComment.vue** | 結果表示コンポーネント | 生成コメント表示・履歴・コピー機能 |
| **components/WeatherData.vue** | 天気情報コンポーネント | 現在・予報天気データ・詳細情報表示 |
| **composables/useApi.ts** | API通信層 | REST API呼び出し・エラーハンドリング・ローディング状態 |
| **constants/locations.ts** | 地点データ | 全国地点の座標・名称・地域分類 |
| **constants/regions.ts** | 地域データ | 地域別表示順・カテゴリ分類 |
| **types/index.ts** | 型定義 | TypeScript型・API仕様・UI状態の型定義 |

### 🔄 状態管理

```typescript
// pages/index.vue での主要な状態
const selectedLocation = ref<Location | null>(null)
const generatedComment = ref<GeneratedComment | null>(null)
const isGenerating = ref(false)
const error = ref<string | null>(null)
```

### 🌐 API通信

```typescript
// composables/useApi.ts
export const useApi = () => {
  // 地点一覧取得
  const getLocations = async (): Promise<Location[]>
  
  // コメント生成
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // 生成履歴取得
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### 🎯 UI機能詳細

#### LocationSelection.vue
- **地域フィルタ**: 北海道、東北、関東等の地域別表示
- **検索機能**: 地点名による絞り込み検索
- **お気に入り**: よく使う地点の保存・優先表示
- **レスポンシブ**: モバイル・タブレット対応

#### GenerateSettings.vue
- **LLMプロバイダー選択**: OpenAI・Gemini・Anthropic
- **APIキー状態表示**: 設定済みプロバイダーのアイコン表示
- **生成オプション**: 詳細設定（将来拡張用）

#### GeneratedComment.vue
- **コメント表示**: 天気コメント・アドバイス両方表示
- **コピー機能**: ワンクリックでクリップボードにコピー
- **生成履歴**: 過去の生成結果を時系列表示
- **エクスポート**: CSV形式でのダウンロード

#### WeatherData.vue
- **現在天気**: リアルタイム天気情報
- **12時間予報**: デフォルト予報時刻の詳細表示
- **気温推移**: グラフィカルな温度変化表示
- **警報情報**: 悪天候時の注意喚起表示

## 🚀 使用方法

### Vue.js フロントエンド（推奨）

```bash
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 地点選択から目的の地点を選択
3. LLMプロバイダーを選択
4. 「コメント生成」ボタンをクリック
5. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルから地点とLLMプロバイダーを選択
3. 「コメント生成」ボタンをクリック
4. 生成されたコメントと詳細情報を確認

### プログラマティック使用

```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# 単一地点のコメント生成
result = run_comment_generation(
    location_name="東京",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"生成コメント: {result['final_comment']}")
```

## 🖥️ よく使うコマンド

```bash
# アプリ起動
uv run ./start_api.sh                   # FastAPI + フロントエンド
uv run streamlit run app.py             # Streamlit UI（デバッグ用）

# 開発ツール
uv run pytest                           # テスト実行
make lint                               # コード品質チェック
make format                             # コードフォーマット

# メンテナンス
make clean                              # 一時ファイル削除
uv sync                                 # 依存関係更新
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

## 🎨 開発ツール

### コード品質
```bash
make lint                               # コード品質チェック
make format                             # コードフォーマット
make type-check                         # 型チェック
```

### 設定済みツール
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

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
- **バージョン**: 1.1.0
- **ライセンス**: MIT
- **最終更新**: 2025-06-15
- **開発チーム**: WNI Team

## 🎯 パフォーマンス

- **応答時間**: 平均3-5秒（地点あたり）
- **精度**: 過去データベースとの適合性90%+
- **対応地点**: 全国1000+地点
- **LLMプロバイダー**: 3社対応

## 🔄 更新履歴

- **v1.1.1** (2025-06-15): LLM選択機能修正・タイムゾーン問題解決・プロンプト最適化
- **v1.1.0** (2025-06-15): FastAPI統合・フロントエンド分離完了・PastComment修正
- **v1.0.0** (2025-06-12): Phase 4完了 - Vue.js/Nuxt.jsフロントエンド実装
- **v0.3.0** (2025-06-06): Phase 2完了 - LangGraphワークフロー実装

### 🐛 修正内容 (v1.1.1)

**LLM選択機能の修正:**
- `comment_selector.py`: LLMAPIコール時の引数不整合を修正
- プロンプト改善で確実な数値選択を実現
- 天気・アドバイス両コメントでLLM選択が正常動作

**タイムゾーン問題の修正:**
- timezone-aware/naive datetime混在エラーを解決
- 時系列データ取得の安定性向上
- 予報データ間隔を3-6時間に最適化

**システム改善:**
- エラーハンドリングの強化
- ログ出力の詳細化
- 例外クラスの新設

**動作確認済み:**
- ✅ 天気コメント: LLMによる適切な選択
- ✅ アドバイスコメント: 34番「お出かけＯＫ」選択成功
- ✅ 最終出力: 「昼間は穏やか　お出かけＯＫ」生成確認

## 🤝 コントリビューション

1. Issue作成で問題報告・機能要望
2. Fork & Pull Request での貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 🔧 トラブルシューティング

### よくある問題

**依存関係の競合**
```bash
# 環境をリセット
make clean-venv
make setup
```

**APIキーエラー**
- `.env`ファイルにAPIキーが正しく設定されているか確認
- 環境変数が読み込まれているか確認: `echo $OPENAI_API_KEY`

**天気データ取得エラー**
- WXTECH_API_KEYが正しく設定されているか確認
- ネットワーク接続を確認

**LLMプロバイダーエラー**
- 選択したプロバイダーのAPIキーが設定されているか確認
- APIの利用制限に達していないか確認

## 📞 サポート

問題や質問がございましたら、GitHubのIssuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**