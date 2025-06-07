# Streamlit UI

## 概要

天気コメント生成システムのWebベースユーザーインターフェース（Streamlit実装）

## 主要機能

### 🏠 メインページ
- **地点選択**: ドロップダウン + 検索機能
- **LLMプロバイダー選択**: OpenAI/Gemini/Anthropic
- **リアルタイム生成**: プログレスバー付き
- **結果表示**: コピー・再生成・保存機能

### 📊 統計・分析
- **生成統計**: 回数・成功率・時系列分析
- **地点別分析**: 使用頻度・地域パターン
- **パフォーマンス**: 実行時間・エラー分析
- **可視化**: グラフ・チャート・ダッシュボード

### ⚙️ 設定管理
- **APIキー設定**: 各プロバイダーのキー管理
- **システム設定**: タイムアウト・リトライ回数
- **デバッグ**: 詳細ログ・エラー情報

## ファイル構成

```
├── app.py                          # メインアプリケーション
├── src/ui/
│   ├── streamlit_components.py     # UIコンポーネント
│   ├── streamlit_utils.py          # ユーティリティ関数
│   └── pages/
│       └── statistics.py           # 統計・分析ページ
├── .streamlit/
│   └── config.toml                 # Streamlit設定
├── requirements-streamlit.txt      # Streamlit依存関係
└── docs/
    └── streamlit_guide.md          # 実行ガイド
```

## クイックスタート

```bash
# 依存関係インストール
pip install -r requirements-streamlit.txt

# アプリケーション起動
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセス

## 主要コンポーネント

### 1. 地点選択 (`location_selector`)
- 地点一覧の動的読み込み
- 検索・フィルタリング機能
- お気に入り地点の管理

### 2. LLMプロバイダー選択 (`llm_provider_selector`)
- 複数プロバイダー対応
- プロバイダー情報の表示
- 動的切り替え

### 3. 結果表示 (`result_display`)
- 生成コメントの表示
- メタデータ情報
- アクションボタン（コピー・再生成・保存）

### 4. 履歴管理 (`generation_history_display`)
- 生成履歴の一覧表示
- 詳細情報の展開
- エクスポート機能

## データフロー

```
地点選択 → LLM選択 → 生成実行 → 結果表示 → 履歴保存
    ↓            ↓          ↓         ↓         ↓
   CSV読込    API設定    ワークフロー  UI更新   JSON保存
```

## 設定・カスタマイズ

### テーマ設定
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
```

### APIキー管理
```python
# セッション状態でAPIキーを管理
st.session_state.openai_api_key = "your-key"
```

### 履歴管理
```json
// data/generation_history.json
{
  "timestamp": "2025-06-07T12:00:00",
  "location": "東京",
  "final_comment": "今日は晴れです"
}
```

## 技術仕様

- **フレームワーク**: Streamlit 1.28+
- **可視化**: Plotly, Altair
- **データ処理**: Pandas, NumPy
- **状態管理**: Streamlit Session State
- **ファイル処理**: JSON, CSV

## デプロイメント

### Streamlit Cloud
```bash
# リポジトリをStreamlit Cloudに接続
# requirements-streamlit.txtで依存関係管理
# SecretsでAPIキー設定
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements-streamlit.txt .
RUN pip install -r requirements-streamlit.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## パフォーマンス最適化

- **キャッシュ活用**: `@st.cache_data`で データ読み込み最適化
- **セッション管理**: 必要最小限の状態保持
- **非同期処理**: プログレスバーでUX向上
- **データ制限**: 履歴1000件まで自動管理

## セキュリティ

- **APIキー保護**: セッション状態での暗号化
- **入力検証**: 地点名・パラメータのサニタイズ
- **エラーハンドリング**: 適切なエラー表示

## 今後の拡張

- [ ] **マルチページ対応**: より複雑なナビゲーション
- [ ] **リアルタイム更新**: WebSocket通信
- [ ] **チーム機能**: ユーザー管理・共有機能
- [ ] **A/Bテスト**: 複数モデルの比較機能
- [ ] **API統合**: 外部天気データの直接取得

## トラブルシューティング

**Q: アプリが起動しない**
A: ポート8501が使用中の可能性。`--server.port 8502`で別ポート使用

**Q: 地点データが表示されない**
A: `data/Chiten.csv`の存在とフォーマットを確認

**Q: APIキーエラー**
A: サイドバーの設定パネルでキーを正しく入力

詳細は [Streamlit実行ガイド](../docs/streamlit_guide.md) を参照
