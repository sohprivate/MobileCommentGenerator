# MobileComment Generator Frontend

Nuxt 3 + TypeScript + Vue 3を使用した天気コメント生成システムのフロントエンドアプリケーションです。

## 機能

- 📍 **地点選択**: 日本全国の地点から複数選択可能
- 🌤️ **天気データ入力**: 手動入力またはWxTech API経由での取得
- ⚙️ **生成設定**: コメント生成方法、数、詳細オプションの設定
- 💬 **コメント生成**: LangGraphベースのバックエンドでコメント自動生成
- 📋 **ワンクリックコピー**: 生成されたコメントを簡単にコピー

## 技術スタック

- **フレームワーク**: Nuxt 3
- **言語**: TypeScript
- **UIライブラリ**: Vue 3 Composition API
- **スタイリング**: Scoped CSS
- **API通信**: Nuxt $fetch

## セットアップ

### 前提条件

- Node.js 18以上
- npm または yarn
- バックエンドAPI（Streamlit + FastAPI）が起動していること

### インストール

```bash
# 依存関係のインストール
npm install
```

### 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してAPIのURLを設定
# NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 開発

### 開発サーバーの起動

```bash
# 開発サーバーを起動 (http://localhost:3000)
npm run dev
```

### TypeScriptの型チェック

```bash
npm run typecheck
```

## プロダクションビルド

```bash
# プロダクション用ビルド
npm run build

# ビルドのプレビュー
npm run preview
```

## プロジェクト構造

```
src/tool_design/
├── components/          # Vueコンポーネント
│   ├── LocationSelection.vue    # 地点選択
│   ├── WeatherData.vue         # 天気データ入力
│   ├── GenerateSettings.vue    # 生成設定
│   └── GeneratedComment.vue    # 生成結果表示
├── composables/         # Composition API
│   └── useApi.ts              # API通信
├── constants/           # 定数定義
│   └── locations.ts           # 地点データ
├── types/              # TypeScript型定義
│   └── index.ts              # 共通型定義
├── pages/              # ページコンポーネント
│   └── index.vue             # メインページ
├── public/             # 静的ファイル
│   └── 地点名.csv           # 地点データCSV
└── nuxt.config.ts      # Nuxt設定
```

## API統合

このフロントエンドは以下のAPIエンドポイントを使用します：

- `GET /api/locations` - 地点データの取得
- `POST /api/weather` - 天気データの取得
- `POST /api/generate-comments` - コメント生成

詳細は[STREAMLIT_INTEGRATION.md](./STREAMLIT_INTEGRATION.md)を参照してください。

## カスタマイズ

### 新しい生成方法の追加

`components/GenerateSettings.vue`の`method`オプションに追加：

```vue
<option value="new-method">新しい方法</option>
```

### 地点データの更新

1. `public/地点名.csv`を更新
2. または`constants/locations.ts`の`AREA_MAPPINGS`を編集

### スタイルのカスタマイズ

各コンポーネントの`<style scoped>`セクションでカラーやレイアウトを調整可能です。

## トラブルシューティング

### APIに接続できない場合

1. バックエンドが起動しているか確認
2. `.env`の`NUXT_PUBLIC_API_BASE_URL`が正しいか確認
3. CORSエラーの場合はバックエンドのCORS設定を確認

### 地点データが表示されない場合

1. ブラウザのコンソールでエラーを確認
2. APIが利用できない場合は自動的にCSVファイルから読み込まれます

## ライセンス

MIT