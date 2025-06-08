# 天気予報コメント生成プロジェクト

LangGraphとLLMを活用した天気コメント自動生成システムです。指定した各地点の天気予報データと過去のコメントデータをもとに、LLM（大規模言語モデル）を活用して短い天気コメント（約15文字）を自動生成します。

## 主な特徴
- **LangGraphワークフロー**: 状態遷移と再検討ロジックを体系的に記述
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応
- **頻度ベース選択**: 過去コメントから最適なペアを選択
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **リアルタイムUI**: StreamlitによるWeb UIの実装

## 🚀 現在の進捗状況（2025/6/7時点）

### ✅ Phase 1: 基礎機能（100%完了）
- [x] **地点データ管理システム**: CSV読込・曖昧検索・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合
- [x] **S3過去コメント取得**: JSON解析・頻度検索
- [x] **LLM統合**: マルチプロバイダー対応

### ✅ Phase 2: LangGraphワークフロー（100%完了）✨ NEW
- [x] **SelectCommentPairNode**: コサイン頻度ベースによる選択 ✨ 
- [x] **EvaluateCandidateNode**: 4つの評価基準による検証 ✨ 
- [x] **基本ワークフロー**: 実装済みノードでの骨格実装 ✨ 
- [x] **InputNode/OutputNode**: 本実装完了 ✨ 
- [x] **GenerateCommentNode**: LLM統合実装 ✨ 
- [x] **統合テスト**: エンドツーエンドテスト実装 ✨ 
- [x] **ワークフロー可視化**: 実行トレース・記録ツール ✨ 

### 🚧 Phase 3: UI実装（0%完了）
- [ ] **Streamlit UI**: Web UIの実装
- [ ] **API実装**: RESTful APIエンドポイント

### 🚀 Phase 4: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🔄 システムの主要フロー

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│ InputNode    │────│ FetchForecastNode │────│ RetrievePastCommentsNode │
└──────────────┘    └──────────────────┘    └─────────────────────────┘
                                                          │
      ┌───────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────┐
│ SelectCommentPair │ ✨ 実装完了
└─────────────────┘
      │
      ▼
┌──────────────────┐  Failure  ┌─────────────────────┐
│ EvaluateCandidate│──────────▶│ SelectCommentPair │
└──────────────────┘           └─────────────────────┘
      │ Success               （リトライループ）
      ▼
┌─────────────────┐
│ GenerateComment │ ✨ 実装完了
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ OutputNode      │
└─────────────────┘
```

## 🛠️ 技術スタック

### バックエンド
- **Python 3.10+**
- **LangGraph**: ワークフロー管理
- **Streamlit**: Web UI
- **boto3**: AWS S3連携
- **requests/aiohttp**: API通信

### LLMプロバイダー
- **OpenAI API**
- **Google Gemini API**
- **Anthropic Claude API**

### データソース
- **Weathernews WxTech API**: 12h/24h予報
- **S3バケット**: 過去コメントJSON
- **地点リストCSV**: Chiten.csv

## 🚀 セットアップ

### 前提条件
- Python 3.10以上
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

## 📌 主要機能

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
pytest tests/test_workflow_integration.py
```

## 🗂️ プロジェクト構造

```
.
├── src/
│   ├── data/               # データクラス・管理
│   ├── apis/               # 外部API連携
│   ├── repositories/       # データリポジトリ
│   ├── nodes/              # LangGraphノード
│   ├── workflows/          # ワークフロー実装
│   ├── algorithms/         # 頻度選択計算アルゴリズム ✨ NEW
│   ├── llm/                # LLM統合
│   ├── ui/                 # Streamlit UI
│   └── config/             # 設定管理
├── tests/                  # テストスイート
├── scripts/                # ユーティリティスクリプト
├── docs/                   # ドキュメント
└── examples/               # 使用例
```

## 🔍 プロジェクト問題分析レポート

### 📋 調査結果（2025年6月8日時点）

**重要度: 高** の問題
1. **リポジトリ名の不一致**: `MobileCOmmentGenerator` → `MobileCommentGenerator` への統一推奨
2. **プロジェクト構造の混乱**: `src/tool_design/` 内のVue.js/Nuxt.jsファイルが混在
3. **大容量ファイル**: `package-lock.json` (401KB) がPythonプロジェクトに含まれている

**重要度: 中** の問題
4. **Import文の問題**: 相対importの使用により、テスト実行時にエラーのリスク
   ```python
   # 問題: src/ui/streamlit_components.py
   from .streamlit_utils import load_locations  # 相対import
   
   # 推奨
   from src.ui.streamlit_utils import load_locations  # 絶対import
   ```
5. **ファイル配置**: `Chiten.csv` がルートディレクトリに配置されている
6. **設定ファイル重複**: `.env.example` がルートと `src/tool_design/` に存在

**重要度: 低** の問題
7. **依存関係の分散**: 複数のrequirementsファイルによる管理の複雑化

### 🛠️ 推奨改善アクション

#### 優先度: 高
1. **フロントエンド分離または明確化**
2. **Import文の絶対importへの統一**

#### 優先度: 中  
3. **ファイル整理**: `Chiten.csv` → `src/data/`
4. **重複設定ファイルの統一**

#### 優先度: 低
5. **依存関係管理の最適化**

> **注記**: これらの問題は現在の機能には影響しませんが、コードの保守性と将来の拡張性向上のため修正を推奨します。

## 🔧 最近の更新（2025/6/7）

### Phase 2 完了！ 🎉
1. **ワークフロー統合完了**
   - 全7ノードの本実装完了
   - リトライルーク・エラーハンドリング強化
   - デバッグ情報出力機能

2. **パフォーマンス改善**
   - ノード実行時間測定機能追加
   - 実行トレース・可視化ツール
   - デバッグ情報出力機能

3. **ドキュメント整備**
   - ワークフロー図更新
   - 実行サンプルスクリプト
   - 統合テスト完整

### 次の優先事項
1. Streamlit UI実装（Issue #3）
2. API実装
3. パフォーマンス最適化
4. AWSデプロイメント準備

## 🎁 コントリビューション

1. Issueの確認と選択
2. ブランチ作成: `feature/issue-{number}-{description}`
3. テスト作成（TDD推奨）
4. PR作成とレビュー依頼

詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## 📜 ライセンス

MIT License

## 👥 開発チーム

- **Project Lead**: @sakamo-wni
- **Contributors**: @ah925

---

**Last Updated**: 2025/06/08  
**Status**: Active Development - Phase 2 Complete! 🎉