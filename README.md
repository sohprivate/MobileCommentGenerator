v.lock                                 # uvロックファイル
├── requirements.txt                        # 従来の依存関係ファイル
├── pytest.ini                             # pytest設定
├── mypy.ini                                # mypy設定
├── Makefile                                # ビルド・実行スクリプト
├── setup.sh                               # セットアップスクリプト
└── README.md                               # このファイル
```

## 🛠️ 主要特徴

- **LangGraphワークフロー**: 状態管理とエラーハンドリングロジックを体系的に実装
- **マルチLLMプロバイダー**: OpenAI/Gemini/Anthropic対応  
- **適応性ベース選択**: 過去コメントから最適なペアを適応性に基づいてLLM選択
- **表現ルール遵守**: NG表現禁止・値域制限・文字数規制の自動チェック
- **12時間周期天気予報**: デフォルトで12時間周期のデータを使用
- **デュアルUI実装**: Streamlit（開発用）+ Vue.js/Nuxt.js（本格用）+ React（新規）
- **FastAPI統合**: RESTful APIでフロントエンドとバックエンドを分離
- **天気予報キャッシュ**: 効率的な天気データ管理とキャッシュ機能

## 📈 現在の進捗状況

### ✅ Phase 1: 基盤システム（100%完了）
- [x] **地点データ管理システム**: CSV読み込み・検索・条件取得機能
- [x] **天気予報API機能**: WxTech API統合（12時間周期データ対応）
- [x] **過去コメント取得**: enhanced50.csvベースのデータ解析・類似度選択検証
- [x] **LLM統合**: マルチプロバイダー対応（OpenAI/Gemini/Anthropic）

### ✅ Phase 2: LangGraph ワークフロー（100%完了）
- [x] **SelectCommentPairNode**: コメント類似度選択ベースによる適応選択
- [x] **EvaluateCandidateNode**: 複数の評価基準による検証
- [x] **基盤ワークフロー**: 実装済みノードでの頑健実装
- [x] **InputNode/OutputNode**: 本実装完了
- [x] **GenerateCommentNode**: LLM統合実装
- [x] **統合テスト**: エンドtoエンドテスト状態管理

### ✅ Phase 3: Streamlit UI（100%完了）
- [x] **基盤UI実装**: 地点選択・LLMプロバイダー選択・コメント生成
- [x] **詳細情報表示**: 現在・予報天気データ・詳細情報表示
- [x] **バッチ出力**: 複数地点一覧出力機能
- [x] **CSV出力**: 生成結果のエクスポート機能
- [x] **エラーハンドリング**: ユーザーフレンドリーなエラー表示

### ✅ Phase 4: フロントエンド分離（100%完了）
- [x] **フロントエンド分離**: Vue.js/Nuxt.jsを独立プロジェクトに移行
- [x] **プロジェクト進捗の明確化**: frontend/とsrc/の責任分担明確化
- [x] **API実装**: FastAPI RESTful APIエンドポイント完成
- [x] **統合ドキュメント**: フロントエンド・バックエンド連携ガイド
- [x] **UIコンポーネント**: 地点選択・設定・結果表示の完全実装

### 🚧 Phase 5: デプロイメント（0%完了）
- [ ] **AWSデプロイメント**: Lambda/ECS・CloudWatch統合

## 🔥 React版追加実装ガイド

既存のVue版に影響を与えずにReact版を追加する詳細な手順を以下に示します。

### 📋 設計思想

React版の追加により、より広範囲の開発者コミュニティがこのプロジェクトを活用できるようになります。Vue版とReact版は並列で存在し、共通のAPIとロジックを共有しながら異なるUIライブラリで実装されます。

### 🏗️ ディレクトリ構成（追加後の全体像）

React版追加後の推奨構成では、既存のVue版は完全にそのまま保持し、新しく`react-version/`と`shared/`ディレクトリを追加します。

### 📝 実装手順

#### Step 1: 共通ロジックディレクトリの作成

既存プロジェクトに影響を与えないよう、まず共通ロジック用のディレクトリを作成します。

```bash
# ルートディレクトリで実行
mkdir shared
cd shared
npm init -y
npm install typescript @types/node

# 共通型定義の作成
mkdir -p types api utils constants
```

**shared/types/index.ts**:
```typescript
// 既存のVue版と共通の型定義
export interface Location {
  id: string;
  name: string;
  prefecture: string;
  region: string;
  latitude?: number;
  longitude?: number;
}

export interface GenerateSettings {
  location: Location;
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  temperature?: number;
  targetDateTime?: string;
}

export interface GeneratedComment {
  id: string;
  comment: string;
  adviceComment?: string;
  weather: WeatherData;
  timestamp: string;
  confidence: number;
  location: Location;
  settings: GenerateSettings;
}

export interface WeatherData {
  current: CurrentWeather;
  forecast: ForecastWeather[];
  trend?: WeatherTrend;
}

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  pressure: number;
  windSpeed: number;
  windDirection: string;
  description: string;
  icon: string;
}

export interface ForecastWeather {
  datetime: string;
  temperature: {
    min: number;
    max: number;
  };
  humidity: number;
  precipitation: number;
  description: string;
  icon: string;
}

export interface WeatherTrend {
  trend: 'improving' | 'worsening' | 'stable';
  confidence: number;
  description: string;
}
```

**shared/api/client.ts**:
```typescript
import axios, { AxiosInstance } from 'axios';
import { Location, GenerateSettings, GeneratedComment } from '../types';

export class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:3000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // リクエスト・レスポンスインターセプター
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async getLocations(): Promise<Location[]> {
    const response = await this.client.get('/api/locations');
    return response.data;
  }

  async generateComment(settings: GenerateSettings): Promise<GeneratedComment> {
    const response = await this.client.post('/api/generate', settings);
    return response.data;
  }

  async getHistory(limit: number = 10): Promise<GeneratedComment[]> {
    const response = await this.client.get('/api/history', {
      params: { limit },
    });
    return response.data;
  }

  async getWeatherData(locationId: string): Promise<WeatherData> {
    const response = await this.client.get(`/api/weather/${locationId}`);
    return response.data;
  }
}

// シングルトンインスタンス
export const apiClient = new ApiClient();
```

#### Step 2: React版プロジェクトの作成

```bash
# ルートディレクトリで実行
mkdir react-version
cd react-version

# Vite + React + TypeScriptプロジェクトを作成
npm create vite@latest . -- --template react-ts

# 基本依存関係をインストール
npm install

# 追加ライブラリのインストール
npm install axios lucide-react clsx
npm install -D tailwindcss postcss autoprefixer @types/react @types/react-dom

# Tailwind CSSを初期化
npx tailwindcss init -p
```

**react-version/tailwind.config.js**:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
```

#### Step 3: React版コンポーネントの実装

**react-version/src/components/LocationSelection.tsx**:
```tsx
import React, { useState, useEffect } from 'react';
import { Search, MapPin, Loader2 } from 'lucide-react';
import { Location } from '../../../shared/types';
import { apiClient } from '../../../shared/api/client';

interface LocationSelectionProps {
  selectedLocation: Location | null;
  onLocationChange: (location: Location) => void;
  className?: string;
}

export const LocationSelection: React.FC<LocationSelectionProps> = ({
  selectedLocation,
  onLocationChange,
  className = '',
}) => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.getLocations();
        setLocations(data);
      } catch (err) {
        setError('地点データの取得に失敗しました');
        console.error('Failed to fetch locations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();
  }, []);

  const filteredLocations = locations.filter(location =>
    location.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.prefecture.toLowerCase().includes(searchTerm.toLowerCase()) ||
    location.region.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
          <span className="ml-2 text-gray-600">読み込み中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <label htmlFor="location-search" className="block text-sm font-medium text-gray-700 mb-2">
          地点選択
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            id="location-search"
            type="text"
            placeholder="地点名または地域名で検索..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {selectedLocation && (
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-primary-600" />
            <div>
              <div className="font-medium text-primary-900">{selectedLocation.name}</div>
              <div className="text-sm text-primary-700">{selectedLocation.prefecture} - {selectedLocation.region}</div>
            </div>
          </div>
        </div>
      )}
      
      <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
        {filteredLocations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            検索条件に一致する地点が見つかりません
          </div>
        ) : (
          filteredLocations.map((location) => (
            <button
              key={location.id}
              className={`w-full text-left p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 flex items-center space-x-2 transition-colors ${
                selectedLocation?.id === location.id ? 'bg-primary-50' : ''
              }`}
              onClick={() => onLocationChange(location)}
            >
              <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900 truncate">{location.name}</div>
                <div className="text-sm text-gray-500 truncate">{location.prefecture} - {location.region}</div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};
```

**react-version/src/hooks/useApi.ts**:
```tsx
import { useState, useCallback } from 'react';
import { apiClient } from '../../../shared/api/client';
import { GenerateSettings, GeneratedComment, Location } from '../../../shared/types';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateComment = useCallback(async (
    location: Location,
    settings: Omit<GenerateSettings, 'location'>
  ): Promise<GeneratedComment> => {
    setLoading(true);
    setError(null);
    
    try {
      const fullSettings: GenerateSettings = {
        location,
        ...settings,
      };
      
      const result = await apiClient.generateComment(fullSettings);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'コメント生成に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getHistory = useCallback(async (limit?: number): Promise<GeneratedComment[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.getHistory(limit);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '履歴の取得に失敗しました';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    generateComment,
    getHistory,
    clearError,
  };
};
```

#### Step 4: ルートpackage.jsonの更新

**package.json（ルート）にスクリプト追加**:
```json
{
  "scripts": {
    "dev": "cd frontend && npm run dev",
    "build": "cd frontend && npm run build",
    "dev:react": "cd react-version && npm run dev",
    "build:react": "cd react-version && npm run build",
    "install:vue": "cd frontend && npm install",
    "install:react": "cd react-version && npm install",
    "install:shared": "cd shared && npm install",
    "install:all": "npm run install:vue && npm run install:react && npm run install:shared",
    "test:vue": "cd frontend && npm run test",
    "test:react": "cd react-version && npm run test",
    "lint:vue": "cd frontend && npm run lint",
    "lint:react": "cd react-version && npm run lint"
  }
}
```

### 🚀 実行方法

#### Vue版（既存）
```bash
# Vue版の依存関係インストール
npm run install:vue

# Vue版開発サーバー起動
npm run dev

# Vue版ビルド
npm run build
```

#### React版（新規）
```bash
# React版の依存関係インストール
npm run install:react

# React版開発サーバー起動
npm run dev:react

# React版ビルド
npm run build:react
```

#### 共通操作
```bash
# 全ての依存関係をインストール
npm run install:all

# 共通ロジックの依存関係インストール
npm run install:shared
```

### 🔧 開発ガイドライン

#### React版コンポーネント設計原則

**1. 関数コンポーネント + Hooks**
```tsx
// ✅ 推奨: 関数コンポーネント
const MyComponent: React.FC<Props> = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // 副作用処理
  }, [dependencies]);

  return <div>...</div>;
};

// ❌ 非推奨: クラスコンポーネント
class MyComponent extends React.Component {
  // 使用しない
}
```

**2. TypeScript必須**
```tsx
// ✅ 推奨: 明確な型定義
interface ComponentProps {
  title: string;
  count: number;
  onUpdate: (value: number) => void;
  optional?: boolean;
}

const Component: React.FC<ComponentProps> = ({ title, count, onUpdate, optional = false }) => {
  // 実装
};

// ❌ 非推奨: any型の使用
const Component = ({ title, count, onUpdate }: any) => {
  // 型安全性が失われる
};
```

この詳細な実装ガイドにより、既存のVue版に全く影響を与えることなく、本格的なReact版を追加できます。共通ロジックの活用により、コード重複を最小限に抑えながら、両フレームワークの特性を活かした実装が可能になります。

## 📊 現在のアップデート内容 (v1.1.5)

**コメント選択ロジックの大幅改善:**

- `comment_selector.py`: LLMによる適応的コメント選択とタイム全員対応実装
- プロンプト改善で確実な数値選択を実装
- 最終出力: 「明日は晴やか」「おでかけ日和です」生成確認

**タイム全員対応の修正:**
- timezone-aware/naive datetime系統エラーを解消
- 時系列データ取得の安全性向上
- 予報データ間隔: 3-6時間間隔での効率的な天気変化追跡

**システム改善:**
- エラーハンドリング強化
- 予報データの精度向上
- プロンプト最適化でLLMレスポンス精度向上

**動作確認済み:**
- 単一地点のコメント生成: LLMによる適応選択成功
- アドバイスコメント: 34種「おでかけ日和」選択成功
- 最終出力: 「明日は晴やか」「おでかけ日和です」生成確認

生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📈 天気コメント改善内容 (v1.1.1)

システムは**翌朝9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。設定された時刻は日本標準時間（JST）です。

### 重複コメント防止機能

**重複パターンの検出:**
- 完全同一の重複検出
- 重複キーワード並び（「にわか雨がちらつく」「にわか雨に注意」等）
- 類似表現パターンマッチング（「雨が心配」↔「雨にご注意」「雨に気をつけて」等）
- 頻度観測における高頻出語彙検出（70%以上の文字共通性など）

**代替選択機能:**
- 重複検出時の自動代替ペア選択
- 最大10回の候補重複検測機能
- カテゴリエバーション（複数パターンがある場合）
- フォールバック機能での効率的な代替利用

**改善例:**
- ❌ Before: 「にわか雨がちらつく」「にわか雨がちらつきます」
- ✅ After: 「にわか雨がちらつく」「水分補給を心がけて」
- ❌ Before: 「熱中症警戒」「熱中症に注意」  
- ✅ After: 「熱中症警戒」「水分補給をお忘れなく」

### 天気の優先順位ルール

1. **特別に慎重な最優先項目**: 雨、雪、雨の3つのうちなどの不適切な天気表現を除去
2. **本日天気の最優先対策**: 重い雨（10mm/h以上）「スッキリしない」表現を阻止  
3. **最高気温35℃以上**: 最高気温最優先で「おでかけ日和」選択成功
4. **その他**: 最高気温データと湿度

### 予報の例

天気↔LLMによる適応選択成功
- 「雨3回」「晴れ1回」「おでかけ日和」選択成功
- 「晴れ2回」「お天気予想1回」選択成功  
- 「真夏日30℃」選択成功

🚨 生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📝 フロントエンド構成

### フロントエンド機能詳細

| ファイル | 役割 | 主要機能 |
|---------|------|----------|
| **pages/index.vue** | メインページ | 全体レイアウト・状態管理・API連携機能 |
| **app.vue** | アプリケーション全体のレイアウト | グローバルスタイル・共通レイアウト |
| **components/LocationSelection.vue** | 地点選択コンポーネント | 地域リスト・検索機能・フィルタリング機能 |
| **components/GenerateSettings.vue** | 設定コンポーネント | LLMプロバイダー選択・生成オプション設定 |
| **components/GeneratedComment.vue** | 結果表示コンポーネント | 生成コメント・履歴・コピー機能 |
| **components/WeatherData.vue** | 天気データコンポーネント | 現在・予報天気データ・詳細情報表示 |
| **composables/useApi.ts** | API層 | REST通信・エラーハンドリング・ローディング状態管理 |
| **constants/locations.ts** | 地点データ | 全国地点リスト |
| **constants/regions.ts** | 地域データ | 地域分類・表示項目・カテゴリ分類 |
| **types/index.ts** | 型定義 | API・UI内の型定義 |

### 状態管理

```typescript
// pages/index.vueでの主要状態管理
const selectedLocation = ref<Location | null>(null)
const generatedComment = ref<GeneratedComment | null>(null)
const isGenerating = ref(false)
const error = ref<string | null>(null)
```

### API通信

```typescript
// composables/useApi.ts
export const useApi = () => {
  // 地点一覧取得
  const getLocations = async (): Promise<Location[]>
  
  // コメント生成
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // 生成履歴取得
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### UI機能詳細

#### LocationSelection.vue
- **フィルタリング**: 北海道・東北・関東・中部・関西・中国・四国・九州など地域別検索機能・フィルタリング機能
- **検索機能**: よく使う地点の保存・手動入力検索機能
- **レスポンシブ**: モバイル・タブレット対応

#### GenerateSettings.vue
- **LLMプロバイダー選択**: OpenAI・Gemini・Anthropic
- **API設定表示**: 温度パラメータ・生成オプション設定
- **プロンプト設定**: カスタムプロンプトテンプレート

#### GeneratedComment.vue
- **コメント表示**: 天気コメント・アドバイスコメント一体表示・コピー機能
- **生成履歴**: 過去の生成コメント一覧・時刻情報・詳細情報表示
- **エクスポート**: CSV出力機能

#### WeatherData.vue
- **現在天気**: リアルタイム天気データ
- **12時間予報**: デフォルトで12時間後のデータを使用
- **気象パラメータ**: 湿度・気圧・風向風速・警戒情報
- **注意報**: 悪天候設定

## 📖 使用方法

### Vue.jsフロントエンド（推奨）

```bash
uv run ./start_api.sh
```

1. ブラウザで http://localhost:3000 を開く
2. 左パネルから地点と天気設定
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### React版フロントエンド（新規）

```bash
# React版開発サーバー起動
npm run dev:react
```

1. ブラウザで http://localhost:5173 を開く
2. 地点選択から希望の地点を選択
3. 生成設定でLLMプロバイダーを選択
4. 「コメント生成」ボタンをクリック
5. 生成されたコメントと天気情報を確認

### Streamlit UI（開発・デバッグ用）

```bash
uv run streamlit run app.py
```

1. ブラウザで http://localhost:8501 を開く
2. 左パネルからLLMプロバイダーを選択
3. 「🌦️ コメント生成」ボタンをクリック
4. 生成されたコメントと天気情報を確認

### プログラマティック使用

```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# 単一地点のコメント生成
result = run_comment_generation(
    location_name="東京",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"生成コメント: {result['final_comment']}")
```

## 🧪 テスト

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 統合テスト
make test-integration
```

## 📗 開発ツール

### コード品質
- **Black**: コードフォーマッター（100文字）
- **isort**: インポート整理
- **mypy**: 型チェック
- **ruff**: 高速リンター
- **pytest**: テストフレームワーク

### その他便利コマンド
```bash
# セットアップスクリプト使用
chmod +x setup.sh
./setup.sh dev

# メンテナンス
make clean            # 一時ファイル削除
uv sync               # 依存更新

# ログ表示
tail -f logs/llm_generation.log    # LLMジェネレーションログ

# ヘルプ
make help
```

## 📗 API設定

### 必須設定
`.env`ファイルでLLMプロバイダーのAPIキーを設定:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 天気予報データ
WXTECH_API_KEY=your_wxtech_api_key_here

# AWS（オプション）
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## 📱️ 天気予報時刻の設定

システムは**翌朝9:00-18:00（JST）の時間帯**から天気に基づいてコメントを生成します。設定された時刻は日本標準時間（JST）です。

### 天気の優先順位ルール

1. **特別に慎重な最優先項目**: 雨、雪、雨の3つのうちなどの不適切な天気表現を除去
2. **本日天気の最優先対策**: 重い雨（10mm/h以上）「スッキリしない」表現を阻止
3. **最高気温35℃以上**: 最高気温最優先で「おでかけ日和」選択成功
4. **その他**: 最高気温データと湿度

### 予報の例

天気→LLMによる適応選択成功
- 「雨3回」「晴れ1回」「おでかけ日和」選択成功
- 「晴れ2回」「お天気予想1回」選択成功
- 「真夏日30℃」選択成功

🚨 生成されたコメントが地点・天気情報に忠実に適応し変化することを確認

## 📔 コントリビューション

1. Issueを作成で問題報告・機能要望
2. Fork & Pull Requestでの貢献
3. [開発ガイドライン](docs/CONTRIBUTING.md)に従った開発

## 📘 サポート

問題が解決しない場合は、GitHub Issuesで報告してください。

---

**このセットアップガイドで問題が解決しない場合は、GitHub Issuesで報告してください。**