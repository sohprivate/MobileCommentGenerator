import React, { useState } from 'react';
import { Cloud, Sparkles, Sun, Moon } from 'lucide-react';
import type { Location, GeneratedComment } from '@mobile-comment-generator/shared';
import { LocationSelection } from './components/LocationSelection';
import { GenerateSettings } from './components/GenerateSettings';
import { GeneratedCommentDisplay } from './components/GeneratedComment';
import { WeatherDataDisplay } from './components/WeatherData';
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
    <div className="min-h-screen bg-app-bg text-app-text transition-colors">
      {/* ヘッダー */}
      <header className="bg-app-surface shadow-sm border-b border-app-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Cloud className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-app-text">天気コメント生成システム</h1>
              <p className="text-sm text-gray-600 dark:text-gray-300">React版</p>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md border border-transparent hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左パネル: 設定 */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-app-surface rounded-lg shadow-sm border border-app-border p-6">
              <LocationSelection
                selectedLocation={selectedLocation}
                onLocationChange={setSelectedLocation}
              />
            </div>

            <div className="bg-app-surface rounded-lg shadow-sm border border-app-border p-6">
              <GenerateSettings
                llmProvider={llmProvider}
                onLlmProviderChange={setLlmProvider}
                temperature={temperature}
                onTemperatureChange={setTemperature}
              />
            </div>

            {/* 生成ボタン */}
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

            {/* エラー表示 */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* 右パネル: 結果表示 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 生成されたコメント */}
            <div className="bg-app-surface rounded-lg shadow-sm border border-app-border p-6">
              <GeneratedCommentDisplay
                comment={generatedComment}
                onCopy={handleCopyComment}
              />
            </div>

            {/* 天気データ */}
            {generatedComment?.weather && (
              <div className="bg-app-surface rounded-lg shadow-sm border border-app-border p-6">
                <WeatherDataDisplay weather={generatedComment.weather} />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App
