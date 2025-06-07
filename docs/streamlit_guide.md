# Streamlit UI実行ガイド

## 概要

このガイドでは、天気コメント生成システムのStreamlit UIの実行方法を説明します。

## 前提条件

- Python 3.10以上がインストールされていること
- 必要なAPIキー（OpenAI、Gemini、Anthropicのいずれか）
- 依存関係がインストールされていること

## セットアップ

### 1. 依存関係のインストール

```bash
# 基本的な依存関係
pip install -r requirements.txt

# Streamlit専用の依存関係
pip install -r requirements-streamlit.txt
```

### 2. 環境変数の設定（オプション）

```bash
# APIキーを環境変数で設定する場合
export OPENAI_API_KEY="your-openai-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## 実行方法

### 基本実行

```bash
streamlit run app.py
```

### カスタムポート指定

```bash
streamlit run app.py --server.port 8502
```

### ヘッドレスモード（サーバー環境）

```bash
streamlit run app.py --server.headless true --server.port 8501 --server.address 0.0.0.0
```

## アクセス方法

ブラウザで以下のURLにアクセス：
- ローカル: http://localhost:8501
- カスタムポート: http://localhost:8502
- リモート: http://your-server-ip:8501

## UI使用方法

### 1. 初期設定

1. サイドバーの「APIキー設定」を展開
2. 使用するLLMプロバイダーのAPIキーを入力
3. 「APIキーを検証」ボタンで確認

### 2. コメント生成

1. **地点選択**
   - ドロップダウンから地点を選択
   - 検索バーで地点名を検索
   - お気に入り地点の登録・使用

2. **LLMプロバイダー選択**
   - OpenAI (GPT-4)
   - Google Gemini
   - Anthropic Claude

3. **生成実行**
   - 「コメント生成」ボタンをクリック
   - プログレスバーで進行状況を確認
   - 結果が右側パネルに表示

### 3. 結果の操作

- **コピー**: 生成されたコメントをクリップボードにコピー
- **再生成**: 同じ条件で再度生成
- **保存**: 履歴に保存（自動）

### 4. 履歴管理

- サイドバーで過去の生成履歴を確認
- 履歴の詳細表示
- JSONファイルとしてエクスポート

## 機能詳細

### ページ構成

1. **メインページ（ホーム）**
   - 地点選択とLLMプロバイダー選択
   - リアルタイム生成とプログレス表示
   - 結果表示とアクション

2. **統計・分析ページ**
   - 生成履歴の統計情報
   - 地点別・プロバイダー別分析
   - 時系列チャートとパフォーマンス分析

3. **設定ページ**
   - APIキー管理
   - システム設定
   - デバッグオプション

### データ管理

- **履歴保存**: `data/generation_history.json`
- **地点データ**: `data/Chiten.csv`
- **設定**: セッション状態で管理

## トラブルシューティング

### よくある問題

1. **ポートが使用中**
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **APIキーエラー**
   - サイドバーでAPIキーを正しく設定
   - 環境変数の確認

3. **地点データが読み込めない**
   - `data/Chiten.csv`の存在確認
   - ファイル形式の確認

4. **履歴が表示されない**
   - `data/`ディレクトリの作成
   - 権限の確認

### ログ確認

```bash
streamlit run app.py --logger.level debug
```

### パフォーマンス最適化

1. **キャッシュクリア**
   ```bash
   streamlit cache clear
   ```

2. **メモリ使用量削減**
   - 履歴サイズの制限（1000件）
   - セッション状態の最適化

## Docker実行（オプション）

### Dockerfileを使用

```bash
# イメージビルド
docker build -t weather-comment-ui .

# コンテナ実行
docker run -p 8501:8501 weather-comment-ui
```

### docker-compose使用

```yaml
version: '3.8'
services:
  streamlit-ui:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
```

```bash
docker-compose up
```

## デプロイメント

### Streamlit Cloud

1. GitHubリポジトリをStreamlit Cloudに接続
2. `app.py`をメインファイルに指定
3. `requirements-streamlit.txt`で依存関係を管理
4. SecretsでAPIキーを設定

### その他のプラットフォーム

- **Heroku**: `Procfile`を追加
- **AWS EC2**: systemdサービスとして設定
- **GCP Cloud Run**: Dockerコンテナとしてデプロイ

## セキュリティ注意事項

1. **APIキー管理**
   - 本番環境では環境変数を使用
   - Secretsファイルは.gitignoreに追加

2. **アクセス制御**
   - 必要に応じて認証機能を追加
   - ファイアウォール設定の確認

3. **データ保護**
   - 履歴データの暗号化
   - 定期的なバックアップ

## サポート

問題が発生した場合：
1. ログを確認
2. Issueを作成
3. デバッグモードで詳細情報を取得

## 更新履歴

- v1.0.0: 初期実装
- 地点選択、LLMプロバイダー選択
- リアルタイム生成とプログレス表示
- 履歴管理と統計分析
