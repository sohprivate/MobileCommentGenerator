# フロントエンド分離完了

## 移動完了ファイル

### Vueコンポーネント
- src/tool_design/components/LocationSelection.vue → frontend/components/LocationSelection.vue
- src/tool_design/components/WeatherData.vue → frontend/components/WeatherData.vue  
- src/tool_design/components/GenerateSettings.vue → frontend/components/GenerateSettings.vue
- src/tool_design/components/GeneratedComment.vue → frontend/components/GeneratedComment.vue

### ページ
- src/tool_design/pages/index.vue → frontend/pages/index.vue

### Composables
- src/tool_design/composables/useApi.ts → frontend/composables/useApi.ts

### 型定義
- src/tool_design/types/index.ts → frontend/types/index.ts

### 定数
- src/tool_design/constants/locations.ts → frontend/constants/locations.ts

### 設定ファイル
- src/tool_design/package.json → frontend/package.json (削除済み)
- src/tool_design/nuxt.config.ts → frontend/nuxt.config.ts
- src/tool_design/tsconfig.json → frontend/tsconfig.json
- src/tool_design/app.vue → frontend/app.vue
- src/tool_design/.env.example → frontend/.env.example

## 削除対象

src/tool_design/ ディレクトリの完全削除を実行中...
