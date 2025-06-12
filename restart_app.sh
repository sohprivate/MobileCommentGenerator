#!/bin/bash

echo "🔄 Streamlitアプリを再起動します..."

# 既存のStreamlitプロセスを終了
echo "⏹️  既存のプロセスを停止..."
pkill -f streamlit || true

# Pythonキャッシュをクリア
echo "🧹 キャッシュをクリア..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -rf ~/.streamlit/cache 2>/dev/null || true

# 環境変数を再読み込み
echo "🔑 環境変数を読み込み..."
export $(cat .env | grep -v '^#' | xargs)

# APIキーの確認
echo "✅ API キー確認:"
echo "   OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
echo "   WXTECH_API_KEY: ${WXTECH_API_KEY:0:20}..."

# Streamlitを起動
echo "🚀 Streamlitを起動..."
streamlit run app.py