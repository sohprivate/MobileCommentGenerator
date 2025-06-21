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

interface BatchResult {
  success: boolean;
  location: string;
  comment?: string;
  error?: string;
  metadata?: any;
}

function App() {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'gemini' | 'anthropic'>('gemini');
  const [isBatchMode, setIsBatchMode] = useState(false);
  const [generatedComment, setGeneratedComment] = useState<GeneratedComment | null>(null);
  const [batchResults, setBatchResults] = useState<BatchResult[]>([]);

  const { generateComment, loading, error, clearError } = useApi();
  const { theme, toggleTheme } = useTheme();

  const handleGenerateComment = async () => {
    if (isBatchMode) {
      if (selectedLocations.length === 0) return;
    } else {
      if (!selectedLocation) return;
    }
    
    clearError();
    setGeneratedComment(null);
    setBatchResults([]);
    
    try {
      if (isBatchMode) {
        // Batch generation
        const BATCH_SIZE = 3;
        const results: BatchResult[] = [];
        
        for (let i = 0; i < selectedLocations.length; i += BATCH_SIZE) {
          const chunk = selectedLocations.slice(i, i + BATCH_SIZE);
          const chunkPromises = chunk.map(async (locationName: string) => {
            try {
              // Create a location object for the API
              const locationObj: Location = {
                id: locationName,
                name: locationName,
                prefecture: '',
                region: ''
              };
              
              const result = await generateComment(locationObj, {
                llmProvider,
              });
              
              return {
                success: true,
                location: locationName,
                comment: result.comment,
                metadata: result.metadata
              };
            } catch (error: any) {
              return {
                success: false,
                location: locationName,
                error: error.message || 'コメント生成に失敗しました'
              };
            }
          });

          const chunkResults = await Promise.all(chunkPromises);
          results.push(...chunkResults);
        }
        
        setBatchResults(results);
      } else {
        // Single location generation
        const result = await generateComment(selectedLocation!, {
          llmProvider,
        });
        setGeneratedComment(result);
      }
    } catch (err) {
      console.error('Failed to generate comment:', err);
    }
  };

  const handleCopyComment = (text: string) => {
    navigator.clipboard?.writeText(text);
    console.log('Copied:', text);
  };

  const currentTime = new Date().toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });

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
                  <GenerateSettings
                    llmProvider={llmProvider}
                    onLlmProviderChange={setLlmProvider}
                    isBatchMode={isBatchMode}
                    onBatchModeChange={setIsBatchMode}
                  />
                </div>
              </div>

              <div className="mt-6 bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="p-6">
                  <LocationSelection
                    selectedLocation={selectedLocation}
                    selectedLocations={selectedLocations}
                    onLocationChange={setSelectedLocation}
                    onLocationsChange={setSelectedLocations}
                    isBatchMode={isBatchMode}
                  />
                </div>
              </div>

              {/* 生成時刻表示 */}
              <div className="mt-6 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                <div className="flex items-center text-blue-700 dark:text-blue-300">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium">生成時刻: {currentTime}</span>
                </div>
              </div>

              {/* 生成ボタン */}
              <div className="mt-6">
                <button
                  type="button"
                  onClick={handleGenerateComment}
                  disabled={
                    (isBatchMode && selectedLocations.length === 0) ||
                    (!isBatchMode && !selectedLocation) ||
                    loading
                  }
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
                      <span>{isBatchMode ? '一括コメント生成' : '🌦️ コメント生成'}</span>
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
              {/* 一括生成結果 */}
              {isBatchMode && batchResults.length > 0 && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center mb-4">
                    <Sparkles className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">一括生成結果</h2>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    成功: {batchResults.filter(r => r.success).length}件 / 
                    全体: {batchResults.length}件
                  </div>
                  
                  <div className="space-y-4">
                    {batchResults.map((result, index) => (
                      <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        {result.success ? (
                          <div>
                            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg p-3 mb-3">
                              <div className="flex items-center text-green-700 dark:text-green-300 mb-2">
                                <Sparkles className="w-4 h-4 mr-2" />
                                <span className="font-medium">{result.location} - 生成完了</span>
                              </div>
                              <div className="text-green-800 dark:text-green-200">
                                {result.comment}
                              </div>
                            </div>
                            
                            <button
                              onClick={() => result.comment && handleCopyComment(result.comment)}
                              className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
                            >
                              コピー
                            </button>
                          </div>
                        ) : (
                          <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-3">
                            <div className="flex items-center text-red-700 dark:text-red-300 mb-1">
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                              </svg>
                              <span className="font-medium">{result.location} - 生成失敗</span>
                            </div>
                            <div className="text-red-600 dark:text-red-400 text-sm">
                              {result.error}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 単一生成結果 */}
              {!isBatchMode && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <GeneratedCommentDisplay
                    comment={generatedComment}
                    onCopy={handleCopyComment}
                  />
                </div>
              )}

              {/* 天気データ */}
              {!isBatchMode && generatedComment?.weather && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <WeatherDataDisplay weather={generatedComment.weather} />
                </div>
              )}

              {/* 初期状態 */}
              {!loading && !generatedComment && batchResults.length === 0 && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="text-center py-12">
                    <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <div className="text-lg font-medium text-gray-900 dark:text-white">コメント生成の準備完了</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                      左側のパネルから{isBatchMode ? '地点（複数選択可）' : '地点'}とプロバイダーを選択して、「{isBatchMode ? '一括' : ''}コメント生成」ボタンをクリックしてください
                    </div>
                    
                    {/* Sample Comments */}
                    <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-left">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">サンプルコメント:</div>
                      <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                        <div><strong>晴れの日:</strong> 爽やかな朝ですね</div>
                        <div><strong>雨の日:</strong> 傘をお忘れなく</div>
                        <div><strong>曇りの日:</strong> 過ごしやすい一日です</div>
                        <div><strong>雪の日:</strong> 足元にお気をつけて</div>
                      </div>
                    </div>
                  </div>
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
          <div className="flex flex-col md:flex-row gap-6 justify-center max-w-6xl mx-auto">
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
