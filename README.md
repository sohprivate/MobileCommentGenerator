# 天気予報コメント生成システム ☀️

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地点の天気情報と過去のコメントデータをもとに、LLM（大規模言語モデル）を利用して短い天気コメント（約15文字）を自動生成します。

## 🆕 最新アップデート (2025-06-16)

- **✅ コメント重複検出と代替選択機能**: 天気コメントとアドバイスコメントの重複を検出し、代替ペアを自動選択
- **✅ 天気条件妥当性検証の強化**: 晴天時の「変わりやすい空」表現や31°C以下での「熱中症」表現を制限
- **✅ 意味的矛盾パターン検出**: 「日差し活用」vs「紫外線対策」など矛盾する表現の組み合わせを防止
- **✅ ログレベル最適化**: デバッグ用途のcriticalレベル使用を適切なdebug/infoレベルに修正
- **✅ 文字列置換安全性向上**: 単語境界を考慮した正規表現置換により不自然な置換を防止
- **✅ システム改善**: エラーハンドリング強化とパフォーマンス向上

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## 📗 プロジェクト構成

```
MobileCommentGenerator/
├── src/                               # バックエンドPythonアプリケーション
│   ├── data/                          # データクラス管理
│   │   ├── comment_generation_state.py   # ワークフロー状態管理
│   │   ├── comment_pair.py            # コメントペアデータモデル
│   │   ├── evaluation_criteria.py        # 評価基準定義
│   │   ├── forecast_cache.py          # 天気予報キャッシュ管理
│   │   ├── location_manager.py        # 地点データ管理
│   │   ├── past_comment.py            # 過去コメント管理
│   │   ├── weather_data.py            # 天気データモデル
│   │   ├── weather_trend.py           # 天気傾向分析
│   │   └── Chiten.csv                 # 地点マスターデータ
│   ├── apis/                          # 外部API連携
│   │   └── wxtech_client.py           # WxTech天気API統合
│   ├── algorithms/                    # アルゴリズム実装
│   │   ├── comment_evaluator.py       # コメント評価ロジック
│   │   └── similarity_calculator.py   # 類似度計算
│   ├── nodes/                         # LangGraphノード
│   │   ├── input_node.py              # 入力ノード
│   │   ├── weather_forecast_node.py   # 天気予報取得ノード
│   │   ├── retrieve_past_comments_node.py # 過去コメント取得ノード
│   │   ├── select_comment_pair_node.py    # コメント選択ノード
│   │   ├── comment_selector.py        # コメント選択ロジック
│   │   ├── evaluate_candidate_node.py     # 候補評価ノード
│   │   ├── generate_comment_node.py       # コメント生成ノード
│   │   ├── output_node.py             # 出力ノード
│   │   └── mock_nodes.py              # モックノード（テスト用）
│   ├── workflows/                     # ワークフロー実装
│   │   └── comment_generation_workflow.py
│   ├── llm/                           # LLM統合
│   │   ├── llm_client.py              # LLMクライアント基底
│   │   ├── llm_manager.py             # LLMマネージャー
│   │   ├── prompt_builder.py          # プロンプト構築
│   │   ├── prompt_templates.py        # プロンプトテンプレート
│   │   └── providers/                 # LLMプロバイダー実装
│   │       ├── base_provider.py       # 基底プロバイダー
│   │       ├── openai_provider.py     # OpenAI統合
│   │       ├── gemini_provider.py     # Google Gemini統合
│   │       └── anthropic_provider.py  # Anthropic Claude統合
│   ├── repositories/                  # データリポジトリ
│   │   ├── local_comment_repository.py # ローカルデータアクセス
│   │   └── s3_comment_repository.py   # S3データアクセス
│   ├── utils/                         # ユーティリティ
│   │   ├── common_utils.py            # 共通ユーティリティ
│   │   └── weather_comment_validator.py # 天気コメント検証
│   ├── ui/                            # Streamlit UI
│   │   ├── streamlit_components.py    # UIコンポーネント
│   │   ├── streamlit_utils.py         # UIユーティリティ
│   │   └── pages/                     # マルチページ構成
│   │       └── statistics.py         # 統計情報ページ
│   └── config/                        # 設定管理
│       ├── weather_config.py          # 天気予報設定
│       ├── comment_config.py          # コメント生成設定
│       ├── config_loader.py           # 設定ローダー
│       └── severe_weather_config.py   # 悪天候設定
├── frontend/                          # Vue.js/Nuxt.jsフロントエンド（完全分離）
│   ├── pages/                         # ページコンポーネント
│   │   └── index.vue                  # メインページ（全体レイアウト・状態管理）
│   ├── components/                    # UIコンポーネント
│   │   ├── LocationSelection.vue      # 地点選択（地区別リスト・検索機能）
│   │   ├── GenerateSettings.vue       # 生成設定（LLMプロバイダー選択）
│   │   ├── GeneratedComment.vue       # 生成結果表示（コメント・履歴）
│   │   └── WeatherData.vue            # 天気データ表示（予報情報・評価）
│   ├── composables/                   # Composition API
│   │   └── useApi.ts                  # API呼び出し（REST通信・エラーハンドリング）
│   ├── constants/                     # 定数定義
│   │   ├── locations.ts               # 地点データ（全国地点リスト）
│   │   └── regions.ts                 # 地区データ（地区分類・表示順）
│   ├── types/                         # TypeScript型定義
│   │   └── index.ts                   # API・UI内の型定義
│   ├── app.vue                        # アプリケーション全体のレイアウト
│   ├── nuxt.config.ts                 # Nuxt設定（UIモジュール設定）
│   ├── package.json                   # Node.js依存関係
│   └── start_frontend.sh              # フロントエンド起動スクリプト
├── api_server.py                      # FastAPI APIサーバー
├── app.py                             # Streamlitメインエントリポイント
├── start_api.sh                       # APIサーバー起動スクリプト
├── data/                              # データファイル
│   ├── forecast_cache/                # 天気予報キャッシュ
│   └── generation_history.json       # 生成履歴
├── config/                            # 設定ファイル（YAML）
│   ├── weather_thresholds.yaml        # 天気閾値設定
│   ├── expression_rules.yaml          # 表現ルール
│   ├── ng_words.yaml                  # NGワード
│   └── llm_config.yaml                # LLM設定
├── output/                            # 生成されたCSVファイル・分析結果
├── tests/                             # テストスイート
│   ├── integration/                   # 統合テスト
│   └── test_*.py                      # 各種ユニットテスト
├── docs/                              # ドキュメント
├── scripts/                           # ユーティリティスクリプト
├── examples/                          # サンプルコード
├── pyproject.toml                     # プロジェクト設定・依存関係
├── uv.lock                            # uvロックファイル
├── requirements.txt                   # 従来の依存関係ファイル
├── pytest.ini                        # pytest設定
├── mypy.ini                           # mypy設定
├── Makefile                           # ビルド・実行スクリプト
├── setup.sh                          # セットアップスクリプト
└── README.md                          # このファイル
```

## 🎯 主な特色

- **LangGraphワークフロー**: 状態とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic対応  
- **適応性ベース選択**: 過去コメントから最適なペアを適応性でLLM選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **12時間後天気予報**: デフォルトで12時間後のデータを使用
- **デュアルUI実装**: Streamlit（開発用）+ Vue.js/Nuxt.js（本番用）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能

## 🔧 現在の進捗状況

### ✅ Phase 1: 基礎システム（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・検索・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合（12時間後データ対応）
- [x] **過去コメント取得**: enhanced50.csvベースのデータ解析・類似度選択検索
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント類似度選択ベースによる選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの順次実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト状態管理

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基本UI実装**: 地点選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 現在・予報天気データ・詳細情報表示
- [x] **バッチ出力**: 複数地点一括出力機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### ✅ Phase 4: フロントエンド分離（100%完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト連携の明確化**: frontend/とsrc/の責任分離
- [x] **API実装**: FastAPI RESTful APIエンドポイント完成
- [x] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド
- [x] **UIコンポーネント**: 地点選択・設定・結果表示の完全実装

### 🟡 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 📊 現在のアップデート内容 (v1.1.1)

**コメント選択ロジックの大幅改善:**
- `comment_selector.py`: LLMによる適応的コメント選択とタイムゾーン問題修正
- プロンプト改善で確実な数値選択を実現
- 最終出力: 「明日は穏やかです　お出かけ日和」生成確認

**タイムゾーン問題の修正:**
- timezone-aware/naive datetime系統エラーを解消
- 時系列データ取得の安定性向上
- 予報データ間隔: 3-6時間間隔での効率的な天気変化追跡

**システム改善:**
- エラーハンドリング強化
- 予報データの堅牢性向上
- プロンプト最適化でLLMレスポンス精度向上

**動作確認済み:**
- 単一地点のコメント生成: LLMによる適応選択
- アドバイスコメント: 34種「おでかけ日和」選択成功
- 最終出力: 「明日は穏やかです　おでかけ日和」生成確認

生成されたコメントが地点・天気情報に忠実に適応して変化することを確認

## 📚 天気コメント改善内容 (v1.1.1)

システムは**翌日9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。設定された時刻は日本標準時（JST）です。

### 重複コメント防止機能

**重複パターンの検出:**
- 完全一致の検出
- 重要キーワード重複（にわか雨、熱中症、紫外線等）
- 類似表現パターンマッチング（「雨が心配」→「雨に注意」等）
- 短文での高類似度検出（70%以上の文字共通）

**代替選択機能:**
- 重複検出時の自動代替ペア選択
- 最大10回の試行で重複回避
- 個別バリデーション付き選択
- フォールバック戦略の段階的適用

**改善例:**
- ❌ Before: 「にわか雨が心配　にわか雨に注意」
- ✅ After: 「にわか雨が心配　折り畳み傘を携帯」
- ❌ Before: 「熱中症が心配　熱中症に注意」
- ✅ After: 「熱中症が心配　水分補給を忘れずに」

### 天気条件妥当性検証

**晴天時の制限:**
- 「変わりやすい空」などの不適切な表現を除外
- 31°C以下での「熱中症」表現を制限
- 意味的矛盾パターン検出を追加（「日差し活用」vs「紫外線対策」など）
- 同じ内容の繰り返しコメント防止機能を強化

**システム改善:**
- ログレベル最適化: critical → info/debugに調整
- 文字列置換の安全性向上: 単語境界を考慮した正規表現置換
- 「熱中症対策」→「雨模様対策」などの不自然な置換を防止
- 部分一致による意図しない置換リスクを排除

**動作確認済み:**
- 天気コメント: LLMによる適応選択成功
- アドバイスコメント: 34種「おでかけ日和」選択成功
- 最終出力: 「明日は穏やかです　おでかけ日和」生成確認

### 天気の優先順位ルール

1. **特別な最優先項目**: 雪、曇り、雨、猛暑天（35℃以上）、真夏日（30℃以上）、冷え込み（5℃以下）
2. **本来の気圧要因項目**: 湿気、強い雨、大雨（10mm/h以上），軽い雨（～中雨）、弱い雨（5mm以下）
3. **猛暑日（35℃以上）**: 雲が少なくても暑さを優先
4. **その他**: 最高気温の数値と湿度

### 予報の例

天気コメント：LLMによる適応選択成功
- 「雨が降る3回、雨1回」 → 雨を選択（「抑えつけみ込まれじゃれ」等の一般的コメント）
- 「曇り1回、おぼろ雲多雨1回」 → 曇を選択（「洗濯物は半日」「洗濯物を室内で」等）
- 「猛暑日35℃以上+雲」 → 最高気温を選択（「暑い日を楽しもう」選択成功）
- 「真夏日30℃以上で曇」 → 最高気温を選択（「真夏日を楽しもう」選択成功）

### 設定の確認

設定された時刻は全てのコンポーネントで日本標準時（JST）です。

**注意**: この設定により、すべてのコメントで翌日9時間隔のデータが絶一的に使用されることを確認

## 📄 フロントエンド詳細

### ファイル構成と役割

| ファイル | 役割 | 主な機能 |
|---------|------|----------|
| **pages/index.vue** | メインページ | 全体レイアウト・状態管理 |
| **app.vue** | アプリケーションルート | グローバルスタイル・共通レイアウト |
| **components/LocationSelection.vue** | 地点選択コンポーネント | 地区別リスト・検索機能・フィルタリング機能 |
| **components/GenerateSettings.vue** | 設定コンポーネント | LLMプロバイダー選択・生成オプション設定 |
| **components/GeneratedComment.vue** | 結果表示コンポーネント | 生成コメント表示・履歴・コピー機能 |
| **components/WeatherData.vue** | 天気情報コンポーネント | 現在・予報天気データ・詳細情報表示 |
| **composables/useApi.ts** | API層 | REST API呼び出し・エラーハンドリング・ローディング状態 |
| **constants/locations.ts** | 地点データ | 全国地点の緯度・経度・名称・地区分類 |
| **constants/regions.ts** | 地区データ | 地区分類・表示順・カテゴリ分類 |
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
  // 地点一覧取得
  const getLocations = async (): Promise<Location[]>
  
  // コメント生成
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // 生成履歴取得
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### UI機能詳細

#### LocationSelection.vue
- **フィルタリング**: 北海道・東北・関東などの地区別表示・検索・フィルタリング機能
- **検索機能**: よく使う地点の保存・手動入力検索機能
- **レスポンシブ**: モバイル・タブレット対応メニュー

#### GenerateSettings.vue
- **LLMプロバイダー選択**: OpenAI・Gemini・Anthropic
- **API設定表示**: 設定済みプロバイダーのアイコン表示・設定オプション・生成オプション

#### GeneratedComment.vue
- **コメント表示**: 天気コメント・アドバイス一体表示
- **コピー機能**: ワンクリックでクリップボードにコピー
- **生成履歴**: 過去の生成結果一覧・時系列表示・詳細情報表示
- **エクスポート**: CSVエクスポート機能

#### WeatherData.vue
- **現在天気**: リアルタイム天気情報
- **12時間予報**: デフォルトで12時間後のデータを使用・気温変化・降水量・詳細評価
- **気象パラメータ**: 風速・湿度・注意喚起情報
- **警戒情報**: 悪天候時の注意喚起情報

## 🔧 使用方法

### Vue.jsフロントエンド（推奨）

```bash
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 左パネルから地点と天気設定
3. 「🎯 コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルから地点とLLMプロバイダーを選択
3. 「🎯 コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

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

## 🧪 テスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration
```

## 🔧 開発ツール

### コード品質
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

### その他便利コマンド
```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev

# メンテナンス
make clean           # 一時ファイル削除
uv sync              # 依存関係更新

# ログ表示
tail -f logs/llm_generation.log    # LLMジェネレーションログ

# ヘルプ
make help
```

## 📄 API キー設定

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

## 🌤 天気予報時期の設定

システムは**翌日9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。具体的に以下9:00, 12:00, 15:00, 18:00の4つの時刻の予報を取得し、天気の優先順位に応じて最も適切な予報を選択します。

### 天気の優先順位ルール

1. **特別な最優先項目**: 雪、曇り、雨なのど
2. **本来の雨量**: 軽い雨（にわか雨、熱中症、紫外線等）
3. **猛暑日（35℃以上）**: 雨が少なくても暑さ優先、熱中症対策が特優先
4. **雨天**: 最高気温よりも雨量が優先
5. **その他**: 最高気温と湿度

### 予報の例

- **雨3回、曇り1回** → 雨を選択（「抑えつけ込まれと心配」等の発生コメント）
- **曇り2回、にわか雨1回** → にわか雨を選択（「雨時間で心配　折り畳み傘を携帯」等）
- **猛暑日35℃以上曇り1回** → 最高気温を選択（「熱中症を優先　水分補給を忘れずに」選択成功）
- **真夏日30℃以上で曇り** → 最高気温を選択（「夏のため楽しむ　熱中症に注意」選択成功）

🟡 生成されたコメントが地点・天気条件に忠実に適応して変化することを確認

## 💤 コントリビューション

1. Issueを作成で問題報告・機能要望
2. Fork & Pull Requestでの貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 📎 サポート

問題が解決しない場合は、GitHubのIssuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**
