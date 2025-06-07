# Vue UI とバックエンドワークフローの統合ガイド

## 概要

Vue UI（src/tool_design/）とPython バックエンドワークフロー（src/workflows/）の統合手順とテスト方法

## 前提条件

1. **バックエンドワークフロー**: Issue #7で実装済み
2. **Streamlit UI**: Issue #9で実装済み
3. **Vue UI**: Nuxt 3 + TypeScript実装済み

## 統合アーキテクチャ

```
Vue UI (Frontend)
    ↓ HTTP/API calls
FastAPI Backend (src/api/)
    ↓ Function calls  
LangGraph Workflow (src/workflows/)
    ↓ API calls
LLM Providers (OpenAI/Gemini/Anthropic)
```

## API エンドポイント統合

### 1. コメント生成エンドポイント

**Vue UI側** (`composables/useApi.ts`)
```typescript
const response = await $fetch('/api/generate-comment', {
  method: 'POST',
  body: {
    location_name: '東京',
    target_datetime: new Date().toISOString(),
    llm_provider: 'openai',
    generation_settings: {
      include_emoji: true,
      include_advice: false,
      polite_form: true
    }
  }
})
```

**バックエンド側** (想定)
```python
@app.post("/api/generate-comment")
async def generate_comment(request: CommentGenerationRequest):
    workflow = create_comment_generation_workflow()
    result = workflow.invoke({
        "location_name": request.location_name,
        "target_datetime": request.target_datetime,
        "llm_provider": request.llm_provider
    })
    return result
```

### 2. ヘルスチェック・ステータス確認

```typescript
// Vue UI側
const api = useApi()
const isHealthy = await api.checkHealth()
const workflowStatus = await api.checkWorkflowIntegration()
```

## 統合テスト手順

### 1. バックエンド起動確認

```bash
# Streamlit + FastAPI バックエンド起動
cd src/
streamlit run app.py --server.port 8000
```

### 2. Vue UI起動

```bash
# Vue フロントエンド起動
cd src/tool_design/
npm install
npm run dev
```

### 3. 統合動作確認

#### 3.1 基本機能テスト
- [ ] 地点選択UI動作確認
- [ ] 天気データ入力確認
- [ ] 生成設定変更確認

#### 3.2 API統合テスト
- [ ] `/api/locations` エンドポイント接続確認
- [ ] `/api/weather` エンドポイント接続確認  
- [ ] `/api/generate-comment` エンドポイント接続確認

#### 3.3 ワークフロー統合テスト
- [ ] LLMプロバイダー切り替え動作確認
- [ ] 生成プロセスのリアルタイム表示
- [ ] エラーハンドリング確認

## 設定ファイル

### Vue UI側設定 (.env)
```bash
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
NUXT_PUBLIC_ENABLE_MOCK=false
```

### バックエンド側設定
```python
# API CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Vue UI
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## トラブルシューティング

### CORS エラー
```bash
Access to fetch at 'http://localhost:8000/api/generate-comment' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**解決方法**: バックエンドのCORS設定でVue UIのオリジンを許可

### API エンドポイント不一致
```bash
404 Not Found: /api/generate-comment
```

**確認項目**:
1. バックエンドAPIでエンドポイントが実装されているか
2. URL パスが一致しているか
3. HTTPメソッドが一致しているか

### ワークフロー実行エラー
```bash
500 Internal Server Error: Workflow execution failed
```

**確認項目**:
1. LLM APIキーが正しく設定されているか
2. 必要な依存関係がインストールされているか
3. データベースファイル（過去コメントCSV）が存在するか

## 機能別統合状況

### ✅ 完了済み
- [x] 基本UI構造（Vue 3 + Nuxt 3）
- [x] 地点選択コンポーネント
- [x] 天気データ入力コンポーネント
- [x] 生成設定コンポーネント
- [x] 結果表示コンポーネント
- [x] API通信ロジック（useApi.ts）

### 🔄 統合対応済み
- [x] ワークフロー統合API呼び出し
- [x] LLMプロバイダー切り替え対応
- [x] エラーハンドリング強化

### 📋 テスト必要項目
- [ ] エンドツーエンドテスト実行
- [ ] パフォーマンステスト実行
- [ ] 複数ブラウザでの動作確認

## パフォーマンス最適化

### フロントエンド最適化
```javascript
// ローディング状態管理
const { pending, error, refresh } = await $fetch('/api/generate-comment', {
  lazy: true,
  onRequest: () => showLoading(),
  onResponse: () => hideLoading(),
  onResponseError: (error) => showError(error)
})
```

### バックエンド最適化
```python
# 非同期処理でパフォーマンス向上
async def generate_comment_async(request):
    workflow = create_comment_generation_workflow()
    result = await asyncio.to_thread(workflow.invoke, request)
    return result
```

## 今後の拡張計画

1. **リアルタイム通信**: WebSocketでの進捗リアルタイム表示
2. **キャッシュ機能**: 地点データ・天気データのクライアントサイドキャッシュ
3. **オフライン対応**: PWA化による一部機能のオフライン利用
4. **A/Bテスト**: 複数生成手法の比較機能

## まとめ

Vue UIとバックエンドワークフローの統合により、以下が実現されています：

- **統一されたUX**: StreamlitとVueの2つのUIオプション
- **柔軟なLLM連携**: 複数プロバイダーでの生成テスト
- **スケーラブル構成**: API層での疎結合設計
- **開発効率**: TypeScript型安全性とVueの開発体験

この統合により、Issue #10「React/TypeScriptフロントエンド実装」の要件を**Vue.js/Nuxt.jsベース**で満たすことができます。
