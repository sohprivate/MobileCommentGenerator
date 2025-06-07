# Streamlit UI テスト

このディレクトリには、Streamlit UIの統合テストが含まれています。

## テストファイル構成

- `test_streamlit_app.py` - メインアプリケーションの統合テスト
- `test_streamlit_components.py` - UIコンポーネントの単体テスト
- `test_streamlit_utils.py` - ユーティリティ関数のテスト

## テストの実行方法

### 全てのUIテストを実行
```bash
pytest tests/test_streamlit*.py -v
```

### カバレッジ付きで実行
```bash
pytest tests/test_streamlit*.py -v --cov=app --cov=src/ui --cov-report=html
```

### 特定のテストファイルを実行
```bash
# 統合テストのみ
pytest tests/test_streamlit_app.py -v

# コンポーネントテストのみ
pytest tests/test_streamlit_components.py -v

# ユーティリティテストのみ
pytest tests/test_streamlit_utils.py -v
```

### 特定のテストクラス/関数を実行
```bash
# 特定のクラス
pytest tests/test_streamlit_app.py::TestStreamlitApp -v

# 特定のテスト関数
pytest tests/test_streamlit_app.py::TestStreamlitApp::test_app_loads_without_errors -v
```

## テスト環境の準備

### 必要な依存関係
```bash
pip install streamlit>=1.28.0  # AppTest frameworkが含まれるバージョン
pip install pytest pytest-cov pytest-mock
pip install pyperclip  # クリップボード機能のテスト用
```

### 環境変数の設定（モック用）
```bash
export WXTECH_API_KEY=test-key
export AWS_ACCESS_KEY_ID=test-key
export AWS_SECRET_ACCESS_KEY=test-secret
export S3_COMMENT_BUCKET=test-bucket
export OPENAI_API_KEY=test-key
export GEMINI_API_KEY=test-key
export ANTHROPIC_API_KEY=test-key
```

## Streamlit Testing Framework (AppTest)

Streamlit 1.28.0以降で導入された`streamlit.testing.v1.AppTest`を使用しています。

### 主な機能
- **ヘッドレステスト**: ブラウザを起動せずにアプリをテスト
- **要素の操作**: ボタンクリック、セレクトボックスの選択など
- **状態の検証**: セッション状態、表示内容の確認
- **エラーハンドリング**: 例外の検出とテスト

### 基本的な使用方法
```python
from streamlit.testing.v1 import AppTest

# アプリを読み込んで実行
at = AppTest.from_file("app.py")
at.run()

# 要素を操作
at.button[0].click().run()
at.selectbox[0].select("新しい値").run()

# 結果を検証
assert at.success[0].value == "期待される成功メッセージ"
assert at.session_state["key"] == "期待される値"
```

## モックの使用

外部依存関係（API、データベース、ファイルシステム）はモック化しています：

- **ワークフロー実行**: `src.workflows.comment_generation_workflow.run_comment_generation`
- **地点データ**: `src.data.location_manager.LocationManager`
- **履歴ファイル**: `builtins.open`とファイルI/O
- **クリップボード**: `pyperclip.copy`

## CI/CD統合

GitHub Actionsワークフロー（`.github/workflows/ui-tests.yml`）で自動テストを実行：

- プッシュ/PR時に自動実行
- Python 3.10/3.11でのマトリクステスト
- コードカバレッジ80%以上を要求
- コード品質チェック（ruff, black, isort, mypy）
- セキュリティスキャン

## トラブルシューティング

### `ModuleNotFoundError: No module named 'streamlit.testing'`
Streamlit 1.28.0以降が必要です：
```bash
pip install --upgrade streamlit>=1.28.0
```

### モックが正しく動作しない
パッチのパスが正しいことを確認：
```python
# 正しい: インポート元のパスを指定
@patch('src.workflows.comment_generation_workflow.run_comment_generation')

# 間違い: 使用場所のパスを指定
@patch('app.run_comment_generation')  # これは動作しない
```

### セッション状態のテストが失敗する
AppTestは各`run()`でアプリを再実行します。状態の永続性をテストする場合は、同一のAppTestインスタンス内で操作してください。

## ベストプラクティス

1. **独立性**: 各テストは独立して実行可能にする
2. **モック化**: 外部依存は必ずモック化
3. **明確な名前**: テスト関数名は何をテストしているか明確に
4. **アサーション**: 1つのテストに複数のアサーションは避ける
5. **クリーンアップ**: テスト後の状態をクリーンに保つ
