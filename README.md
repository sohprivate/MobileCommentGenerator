# 天気予報コメント生成プロジェクト

LangGraphとLLMを活用した天気予報コメント自動生成システムです。指定した各地点の天気予報データと過去のコメントデータをもとに、LLM（大規模言語モデル）を活用して短い天気コメント（約15文字）を自動生成します。

## 🏗️ プロジェクト構造（フロントエンド分離済み）

```
mobile-comment-generator/
├── frontend/               # Nuxt.js フロントエンドアプリケーション
│   ├── components/         # Vue.js コンポーネント
│   ├── pages/             # ページルーティング
│   ├── composables/       # Vue Composition API
│   ├── types/             # TypeScript型定義
│   ├── server/            # サーバーサイド機能
│   ├── public/            # 静的アセット
│   ├── package.json       # フロントエンド依存関係
│   ├── nuxt.config.ts     # Nuxt設定
│   └── README.md          # フロントエンド詳細ドキュメント
├── src/                   # バックエンドPythonアプリケーション
│   ├── data/              # データクラス管理
│   ├── apis/              # 外部API連携
│   ├── repositories/      # データリポジトリ
│   ├── nodes/             # LangGraphノード
│   ├── workflows/         # ワークフロー実装
│   ├── algorithms/        # 類似度選択アルゴリズム（新規）
│   ├── llm/               # LLM統合
│   ├── ui/                # Streamlit UI
│   └── config/            # 設定管理
├── tests/                 # テストスイート
├── scripts/               # ユーティリティスクリプト
├── docs/                  # ドキュメント
└── examples/              # 使用例
```

## 主な特徴
- **LangGraphワークフロー**: 状態遷移とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic Claude対応
- **適応ベース選定**: 過去コメントから最適なペアを選定
- **表現ルール適用**: NGワード・文字数制限の自動チェック
- **複合UI実装**: Streamlit（バックエンド）+ Nuxt.js（フロントエンド）

## 🚀 現在の進捗状況（2025/6/8時点）

### ✅ Phase 1: 基礎機能（100%完了）
- [x] **地点データ管理システム**: CSV読込・更新検索・位置情報取得機能
- [x] **天気予報統合機能**: WxTech API統合
- [x] **過去コメント取得**: CSV解析・類似度検索
- [x] **LLM統合**: マルチプロバイダー対応

### ✅ Phase 2: LangGraphワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント類似度ベースによる選定
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基本ワークフロー**: 実装済みノードでの骨格実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト実装
- [x] **ワークフロー可視化**: 実行トレース・記録ツール

### ✅ Phase 3: フロントエンド分離（完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移動
- [x] **プロジェクト構造の明確化**: frontend/とsrc/の責務分離
- [ ] **API実装**: RESTful APIエンドポイント
- [ ] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド

### 🚧 Phase 4: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## セットアップ

### バックエンド
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

### フロントエンド
```bash
# フロントエンドディレクトリへ移動
cd frontend

# 依存関係インストール
npm install

# 開発サーバー起動
npm run dev
```

詳細は各ディレクトリのREADME.mdを参照してください。

---

**Status**: Phase 3 Complete - Frontend Separation! 🎉
