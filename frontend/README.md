# Frontend - Mobile Comment Generator

Nuxt.js ベースのフロントエンドアプリケーション

## 概要

このディレクトリには Mobile Comment Generator のフロントエンドアプリケーションが含まれています。
Nuxt.js を使用してモダンなWeb UIを提供します。

## セットアップ

```bash
cd frontend
npm install
npm run dev
```

## 開発

- 開発サーバー: http://localhost:3000
- ホットリロード対応

## ビルド

```bash
npm run build
npm run start
```

## 構成

- **Nuxt.js**: Vue.js フレームワーク
- **TypeScript**: 型安全な開発
- **TailwindCSS**: ユーティリティファーストCSS

## API連携

バックエンドAPIとの連携については [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) を参照してください。

## ディレクトリ構造

```
frontend/
├── components/          # Vue コンポーネント
├── pages/              # ページコンポーネント
├── composables/        # Composition API
├── types/              # TypeScript型定義
├── server/             # サーバーサイド機能
└── public/             # 静的ファイル
```
