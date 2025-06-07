# Mobile Comment Generator - Makefile
# 開発タスクの自動化

.PHONY: help install install-dev clean test lint format run-streamlit run-frontend setup-env

# デフォルトターゲット
help:
	@echo "Mobile Comment Generator - 利用可能なコマンド:"
	@echo ""
	@echo "セットアップ:"
	@echo "  setup          - 完全な開発環境セットアップ"
	@echo "  install        - 基本依存関係のインストール"
	@echo "  install-dev    - 開発用依存関係のインストール"
	@echo "  setup-env      - 環境変数ファイルの準備"
	@echo ""
	@echo "開発:"
	@echo "  test           - テスト実行"
	@echo "  test-cov       - カバレッジ付きテスト"
	@echo "  lint           - コード品質チェック"
	@echo "  format         - コードフォーマット"
	@echo "  type-check     - 型チェック"
	@echo ""
	@echo "実行:"
	@echo "  run-streamlit  - Streamlit アプリ起動"
	@echo "  run-frontend   - Vue.js フロントエンド起動"
	@echo "  demo           - デモスクリプト実行"
	@echo ""
	@echo "メンテナンス:"
	@echo "  clean          - 一時ファイル削除"
	@echo "  clean-venv     - 仮想環境削除"
	@echo "  update-deps    - 依存関係更新"

# 🚀 セットアップコマンド
setup: clean-venv
	@echo "🚀 完全セットアップを開始..."
	uv venv --python 3.11
	$(MAKE) install-dev
	$(MAKE) setup-env
	@echo "✅ セットアップ完了！"
	@echo "次のステップ: source .venv/bin/activate"

install:
	@echo "📦 基本依存関係をインストール中..."
	uv pip install -r requirements.txt

install-dev:
	@echo "📦 開発用依存関係をインストール中..."
	uv pip install -r requirements.txt -r requirements-dev.txt

setup-env:
	@echo "⚙️  環境変数ファイルを準備中..."
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "✅ .env ファイルを作成しました"; \
			echo "⚠️  APIキーを設定してください"; \
		else \
			echo "❌ .env.example が見つかりません"; \
		fi \
	else \
		echo "ℹ️  .env ファイルは既に存在します"; \
	fi

# 🧪 テストコマンド
test:
	@echo "🧪 テストを実行中..."
	pytest tests/ -v

test-cov:
	@echo "🧪 カバレッジ付きテスト実行中..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-integration:
	@echo "🔗 統合テスト実行中..."
	pytest tests/test_workflow_integration.py -v

# 🎨 コード品質
lint:
	@echo "🔍 コード品質をチェック中..."
	ruff check src/
	flake8 src/
	bandit -r src/

format:
	@echo "🎨 コードをフォーマット中..."
	black src/ tests/ examples/
	isort src/ tests/ examples/
	@echo "✅ フォーマット完了"

type-check:
	@echo "🔍 型チェック実行中..."
	mypy src/

# 🚀 実行コマンド
run-streamlit:
	@echo "🚀 Streamlit アプリを起動中..."
	@echo "ブラウザで http://localhost:8501 を開いてください"
	streamlit run app.py

run-frontend:
	@echo "🚀 Vue.js フロントエンドを起動中..."
	@echo "ブラウザで http://localhost:3000 を開いてください"
	cd src/tool_design && npm run dev

demo:
	@echo "🎮 デモスクリプトを実行中..."
	python examples/location_manager_demo.py
	python examples/workflow_integration_demo.py

# 🧹 メンテナンス
clean:
	@echo "🧹 一時ファイルを削除中..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/
	@echo "✅ クリーンアップ完了"

clean-venv:
	@echo "🧹 仮想環境を削除中..."
	rm -rf .venv
	@echo "✅ 仮想環境削除完了"

update-deps:
	@echo "🔄 依存関係を更新中..."
	uv pip install --upgrade pip
	uv pip install -U -r requirements.txt -r requirements-dev.txt

# 📊 プロジェクト情報
info:
	@echo "📊 プロジェクト情報:"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "uv: $(shell uv --version 2>/dev/null || echo 'Not found')"
	@echo "仮想環境: $(shell echo $$VIRTUAL_ENV || echo 'Not activated')"
	@echo "パッケージ数: $(shell uv pip list 2>/dev/null | wc -l || echo 'N/A')"

# 🔧 開発用ショートカット
dev: setup
	@echo "🛠️  開発環境準備完了"
	@echo "使用可能なコマンド: make lint, make test, make run-streamlit"

quick-test:
	pytest tests/test_location_manager.py -v

quick-lint:
	ruff check src/ --fix