import React from 'react';
import { Settings } from 'lucide-react';

interface GenerateSettingsProps {
  llmProvider: 'openai' | 'gemini' | 'anthropic';
  onLlmProviderChange: (provider: 'openai' | 'gemini' | 'anthropic') => void;
  temperature?: number;
  onTemperatureChange?: (temperature: number) => void;
  className?: string;
}

export const GenerateSettings: React.FC<GenerateSettingsProps> = ({
  llmProvider,
  onLlmProviderChange,
  temperature = 0.7,
  onTemperatureChange,
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
        <h3 className="text-lg font-medium text-gray-900">生成設定</h3>
      </div>

      <div>
        <label htmlFor="llm-provider" className="block text-sm font-medium text-gray-700 mb-2">
          LLMプロバイダー
        </label>
        <select
          id="llm-provider"
          value={llmProvider}
          onChange={(e) => onLlmProviderChange(e.target.value as 'openai' | 'gemini' | 'anthropic')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
          {llmProviders.map((provider) => (
            <option key={provider.value} value={provider.value}>
              {provider.label}
            </option>
          ))}
        </select>
      </div>

      {onTemperatureChange && (
        <div>
          <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-2">
            創造性レベル: {temperature}
          </label>
          <input
            id="temperature"
            type="range"
            min="0.1"
            max="1.0"
            step="0.1"
            value={temperature}
            onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>保守的</span>
            <span>創造的</span>
          </div>
        </div>
      )}

      <div className="bg-gray-50 rounded-lg p-3">
        <h4 className="text-sm font-medium text-gray-700 mb-2">設定について</h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• 各LLMプロバイダーは異なる特性を持ちます</li>
          <li>• 创造性レベルが高いほど多様なコメントが生成されます</li>
          <li>• 保守的な設定では一貫したコメントが生成されます</li>
        </ul>
      </div>
    </div>
  );
};