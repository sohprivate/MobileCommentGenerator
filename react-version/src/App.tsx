import React, { useState } from 'react';
import { Cloud, Sparkles, Sun, Moon } from 'lucide-react';
import type { Location, GeneratedComment } from '@mobile-comment-generator/shared';
import { LocationSelection } from './components/LocationSelection';
import { GenerateSettings } from './components/GenerateSettings';
import { GeneratedCommentDisplay } from './components/GeneratedComment';
import { WeatherDataDisplay } from './components/WeatherData';
import { PricingCard } from './components/PricingCard';
import { useApi } from './hooks/useApi';
import { useTheme } from './hooks/useTheme';

function App() {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'gemini' | 'anthropic'>('gemini');
  const [temperature, setTemperature] = useState(0.7);
  const [generatedComment, setGeneratedComment] = useState<GeneratedComment | null>(null);

  const { generateComment, loading, error, clearError } = useApi();
  const { theme, toggleTheme } = useTheme();

  const handleGenerateComment = async () => {
    if (!selectedLocation) return;
    
    clearError();
    
    try {
      const result = await generateComment(selectedLocation, {
        llmProvider,
        temperature,
      });
      setGeneratedComment(result);
    } catch (err) {
      console.error('Failed to generate comment:', err);
    }
  };

  const handleCopyComment = (text: string) => {
    console.log('Copied:', text);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* ヘッダー */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Sun className="w-8 h-8 text-yellow-500 mr-3" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">天気コメント生成システム</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                React版 v1.0.0
              </span>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md border border-transparent hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左パネル: 設定 */}
            <div className="lg:col-span-1">
              <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center">
                    <Cloud className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">設定</h2>
                  </div>
                </div>
                <div className="p-6">
                  <LocationSelection
                    selectedLocation={selectedLocation}
                    onLocationChange={setSelectedLocation}
                  />
                </div>
              </div>

              <div className="mt-6 bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="p-6">
                  <GenerateSettings
                    llmProvider={llmProvider}
                    onLlmProviderChange={setLlmProvider}
                    temperature={temperature}
                    onTemperatureChange={setTemperature}
                  />
                </div>
              </div>

              {/* 生成ボタン */}
              <div className="mt-6">
                <button
                  onClick={handleGenerateComment}
                  disabled={!selectedLocation || loading}
                  className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>生成中...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      <span>🌦️ コメント生成</span>
                    </>
                  )}
                </button>
              </div>

              {/* エラー表示 */}
              {error && (
                <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4">
                  <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
                </div>
              )}
            </div>

            {/* 右パネル: 結果表示 */}
            <div className="lg:col-span-2 space-y-6">
              {/* 生成されたコメント */}
              <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <GeneratedCommentDisplay
                  comment={generatedComment}
                  onCopy={handleCopyComment}
                />
              </div>

              {/* 天気データ */}
              {generatedComment?.weather && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <WeatherDataDisplay weather={generatedComment.weather} />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* 料金プランセクション */}
      <section className="py-12 bg-gray-100 dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">料金プラン</h2>
          <div className="flex flex-col md:flex-row gap-6 justify-center">
            <PricingCard
              planKey="basic"
              title="Basic"
              price="¥1,000/月"
              features={['基本的な天気予報', '1日10回まで生成', 'メールサポート']}
            />
            <PricingCard
              planKey="pro"
              title="Pro"
              price="¥5,000/月"
              features={['詳細な天気予報', '無制限生成', '優先サポート', 'API アクセス']}
            />
            <PricingCard
              planKey="enterprise"
              title="Enterprise"
              price="お問い合わせ"
              features={['カスタム予報モデル', '専用インフラ', '24/7 サポート', 'SLA 保証']}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

export default App
