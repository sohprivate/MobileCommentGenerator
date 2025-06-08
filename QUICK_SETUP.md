# 🚀 Quick Setup Guide

このガイドでは、MobileCommentGeneratorの環境を最速でセットアップする方法を説明します。

## ⚡ ワンコマンドセットアップ

### Method 1: 自動セットアップスクリプト（推奨）

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. ワンコマンドセットアップ
chmod +x setup.sh
./setup.sh dev

# 3. 仮想環境有効化
source .venv/bin/activate

# 4. 動作確認
python -c "import langgraph; print('✅ Setup successful!')"
```

### Method 2: Makefileを使用

```bash
# 1. リポジトリクローン
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. ワンコマンドセットアップ
make setup

# 3. 仮想環境有効化
source .venv/bin/activate

# 4. 利用可能なコマンド確認
make help
```

## 🔧 手動セットアップ

```bash
# 1. 仮想環境作成
uv venv --python 3.11
source .venv/bin/activate

# 2. 依存関係インストール
uv pip install -r requirements.txt          # 基本版
uv pip install -r requirements-dev.txt      # 開発版

# 3. 環境変数設定
cp .env.example .env
# .envファイルでAPIキーを設定

# 4. 動作確認
streamlit run app.py
```

## 🎯 よく使うコマンド

```bash
# アプリ起動
make run-streamlit              # Streamlit UI
make run-frontend              # Vue.js フロントエンド

# 開発ツール
make test                      # テスト実行
make lint                      # コード品質チェック
make format                    # コードフォーマット

# メンテナンス
make clean                     # 一時ファイル削除
make update-deps              # 依存関係更新
```

## 📦 パッケージ管理

### 依存関係の分離
- `requirements.txt` - 本番環境用の基本依存関係
- `requirements-dev.txt` - 開発環境用の追加依存関係

### uvの活用
- 高速インストール: `uv pip install -r requirements.txt`
- プロジェクト管理: `uv sync`
- Python管理: `uv python install 3.11`

## 🔍 トラブルシューティング

### よくある問題
1. **依存関係の競合**: `langchain-core>=0.1.42`で解決済み
2. **Python バージョン**: 3.10以上が必要
3. **uv未インストール**: セットアップスクリプトが自動インストール

### 完全リセット
```bash
make clean-venv                # 仮想環境削除
make setup                     # 再セットアップ
```

## 📚 次のステップ

1. **APIキー設定**: `.env`ファイルでLLMプロバイダーのAPIキーを設定
2. **アプリ起動**: `make run-streamlit`でWebUIを確認
3. **開発開始**: `make help`で利用可能なコマンドを確認

---

**このセットアップガイドで問題が解決しない場合は、GitHubのIssuesで報告してください。**