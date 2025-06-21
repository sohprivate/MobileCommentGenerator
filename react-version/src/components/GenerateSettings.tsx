import React from 'react';
import { Settings, Globe, MapPin } from 'lucide-react';

interface GenerateSettingsProps {
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  onLlmProviderChange: (provider: 'openai' | 'gemini' | 'anthropic') => void;
  isBatchMode: boolean;
  onBatchModeChange: (isBatch: boolean) => void;
  className?: string;
}

export const GenerateSettings: React.FC<GenerateSettingsProps> = ({
  llmProvider,
  onLlmProviderChange,
  isBatchMode,
  onBatchModeChange,
  className = '',
}) => {
  const llmProviders = [
    { value: 'gemini', label: 'Google Gemini' },
    { value: 'openai', label: 'OpenAI GPT' },
    { value: 'anthropic', label: 'Anthropic Claude' },
  ] as const;

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Settings className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">生成設定</h3>
      </div>

      {/* Batch Mode Toggle */}
      <div className="mb-6">
        <div className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          生成モード
        </div>
        <div className="p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 hover:border-blue-300 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1 flex items-center">
                {isBatchMode ? (
                  <>
                    <Globe className="w-5 h-5 mr-2" />
                    🌏 一括生成モード
                  </>
                ) : (
                  <>
                    <MapPin className="w-5 h-5 mr-2" />
                    📍 単一地点モード
                  </>
                )}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {isBatchMode ? '複数地点を同時に生成します' : '1つの地点のみ生成します'}
              </div>
            </div>
            <button
              onClick={() => onBatchModeChange(!isBatchMode)}
              className={`relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out ${
                isBatchMode ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'
              }`}
              aria-label="Toggle batch mode"
            >
              <span
                className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  isBatchMode ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      <div>
        <label htmlFor="llm-provider" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          LLMプロバイダー
        </label>
        <select
          id="llm-provider"
          value={llmProvider}
          onChange={(e) => onLlmProviderChange(e.target.value as 'openai' | 'gemini' | 'anthropic')}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 transition-colors"
        >
          {llmProviders.map((provider) => (
            <option key={provider.value} value={provider.value}>
              {provider.label}
            </option>
          ))}
        </select>
      </div>

      {/* Weather Forecast Info */}
      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
        <h4 className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2 flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.4 4.4 0 003 15z" />
          </svg>
          天気予報の仕様
        </h4>
        <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
          <li>• 予報時刻: 翌日の9:00, 12:00, 15:00, 18:00（JST）</li>
          <li>• 優先順位: 雷・嵐 &gt; 本降りの雨 &gt; 猛暑日熱中症対策 &gt; 雨 &gt; 曇り &gt; 晴れ</li>
        </ul>
      </div>
    </div>
  );
};