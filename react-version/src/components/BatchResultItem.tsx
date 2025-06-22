import React from 'react';
import { ChevronDown, ChevronUp, CheckCircle, AlertTriangle, Copy, RefreshCw } from 'lucide-react';

interface BatchResult {
  success: boolean;
  location: string;
  comment?: string;
  error?: string;
  metadata?: any;
  weather?: any;
  adviceComment?: string;
}

interface BatchResultItemProps {
  result: BatchResult;
  isExpanded: boolean;
  onToggleExpanded: () => void;
  onRegenerate: () => void;
  isRegenerating: boolean;
}

export const BatchResultItem: React.FC<BatchResultItemProps> = ({
  result,
  isExpanded,
  onToggleExpanded,
  onRegenerate,
  isRegenerating
}) => {
  const handleCopy = () => {
    if (result.comment) {
      navigator.clipboard?.writeText(result.comment);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {result.success ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-red-500" />
          )}
          <h4 className="font-medium text-gray-900 dark:text-white">
            {result.location}
          </h4>
        </div>
        <button
          onClick={onToggleExpanded}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </button>
      </div>

      {result.success && result.comment && (
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          {result.comment}
        </p>
      )}

      {!result.success && result.error && (
        <p className="text-sm text-red-600 dark:text-red-400 mb-2">
          エラー: {result.error}
        </p>
      )}

      <div className="flex items-center space-x-2 mt-3">
        {result.success && result.comment && (
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <Copy className="w-3 h-3" />
            <span>コピー</span>
          </button>
        )}
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-3 h-3 ${isRegenerating ? 'animate-spin' : ''}`} />
          <span>{isRegenerating ? '再生成中...' : '再生成'}</span>
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
          {result.adviceComment && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                アドバイスコメント
              </h5>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {result.adviceComment}
              </p>
            </div>
          )}

          {result.weather && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                天気情報
              </h5>
              <pre className="text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-x-auto">
                {JSON.stringify(result.weather, null, 2)}
              </pre>
            </div>
          )}

          {result.metadata && (
            <div>
              <h5 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                メタデータ
              </h5>
              <pre className="text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-x-auto">
                {JSON.stringify(result.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};