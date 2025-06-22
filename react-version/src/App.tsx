import React, { useState, useEffect, useCallback } from 'react';
import { Cloud, Sparkles, Sun, Moon, AlertTriangle, CheckCircle2, Info, Copy as CopyIcon } from 'lucide-react';
import type { Location, GeneratedComment as SharedGeneratedComment, GenerateSettings } from '@mobile-comment-generator/shared';
import { LocationSelection } from './components/LocationSelection';
import { GenerateSettings as GenerateSettingsComponent } from './components/GenerateSettings';
import { GeneratedCommentDisplay } from './components/GeneratedComment';
import { useApi } from './hooks/useApi';
import { useTheme } from './hooks/useTheme';
import { REGIONS, getAllLocations as getFallbackLocations } from './constants/regions';

interface CommentProcessResult {
  id: string;
  locationName: string;
  status: 'pending' | 'generating' | 'success' | 'error';
  comment?: string;
  error?: string;
  metadata?: any;
}

interface ApiGeneratedComment extends SharedGeneratedComment {
  error?: string;
}

const MAX_BATCH_LOCATIONS = 30;
const WARN_BATCH_LOCATIONS = 20;

function getLocationInfo(locationName: string): Location {
  for (const [regionName, prefectures] of Object.entries(REGIONS)) {
    for (const [prefName, locationsInPref] of Object.entries(prefectures)) {
      if ((locationsInPref as string[]).includes(locationName)) {
        return { id: locationName, name: locationName, prefecture: prefName, region: regionName };
      }
    }
  }
  return { id: locationName, name: locationName, prefecture: '不明', region: '不明' };
}

function App() {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [llmProvider, setLlmProvider] = useState<'openai' | 'gemini' | 'anthropic'>('gemini');
  const [isBatchMode, setIsBatchMode] = useState(false);

  const [singleGeneratedComment, setSingleGeneratedComment] = useState<ApiGeneratedComment | null>(null);
  const [processedComments, setProcessedComments] = useState<CommentProcessResult[]>([]);

  const [appLoading, setAppLoading] = useState(false);
  const [appError, setAppError] = useState<string | null>(null);

  const { generateComment: apiGenerateComment, clearError: clearApiError } = useApi();
  const { theme, toggleTheme } = useTheme();

  const batchErrors = React.useMemo(() => {
    if (isBatchMode) {
      return processedComments.filter(r => r.status === 'error' && r.error);
    }
    return [];
  }, [isBatchMode, processedComments]);

  const batchProgress = React.useMemo(() => {
    if (!isBatchMode || processedComments.length === 0) return null;
    
    const total = processedComments.length;
    const completed = processedComments.filter(r => r.status === 'success' || r.status === 'error').length;
    const success = processedComments.filter(r => r.status === 'success').length;
    const error = processedComments.filter(r => r.status === 'error').length;
    const generating = processedComments.filter(r => r.status === 'generating').length;
    
    return {
      total,
      completed,
      success,
      error,
      generating,
      percentage: Math.round((completed / total) * 100)
    };
  }, [isBatchMode, processedComments]);

  const updateProcessedCommentById = useCallback((locationId: string, updates: Partial<Omit<CommentProcessResult, 'id' | 'locationName'>>) => {
    setProcessedComments(prev =>
      prev.map(item =>
        item.id === locationId ? { ...item, ...updates } : item
      )
    );
  }, []);

  const handleGenerateComment = async () => {
    setAppError(null);
    clearApiError();
    setSingleGeneratedComment(null);
    
    if (isBatchMode) {
      if (selectedLocations.length === 0) {
        setAppError("一括生成する地点を選択してください。");
        return;
      }
      if (selectedLocations.length > MAX_BATCH_LOCATIONS) {
        setAppError(`一度に処理できるのは最大 ${MAX_BATCH_LOCATIONS} 地点までです。`);
        return;
      }

      setAppLoading(true);

      const sortedSelectedLocations = [...selectedLocations].sort();

      const initialResults = sortedSelectedLocations.map(locName => ({
        id: locName,
        locationName: locName,
        status: 'pending' as const,
      }));
      setProcessedComments(initialResults);

      const BATCH_SIZE = 3;

      for (let i = 0; i < sortedSelectedLocations.length; i += BATCH_SIZE) {
        const batch = sortedSelectedLocations.slice(i, i + BATCH_SIZE);

        const batchPromises = batch.map(async (locationName) => {
          updateProcessedCommentById(locationName, { status: 'generating' });
          const locationForApi = getLocationInfo(locationName);

          try {
            const result = await apiGenerateComment(locationForApi, { llmProvider });
            if (result?.comment) {
              updateProcessedCommentById(locationName, {
                status: 'success',
                comment: result.comment,
                metadata: result.metadata,
              });
            } else {
              updateProcessedCommentById(locationName, {
                status: 'error',
                error: 'APIレスポンスが不正です',
              });
            }
          } catch (error: any) {
            console.error(`Failed to generate comment for ${locationName}:`, error);
            updateProcessedCommentById(locationName, {
              status: 'error',
              error: error.message || 'コメント生成に失敗しました',
            });
          }
        });

        await Promise.allSettled(batchPromises);
      }
      setAppLoading(false);

    } else {
      if (!selectedLocation) {
        setAppError("地点を選択してください。");
        return;
      }
      setAppLoading(true);
      setProcessedComments([]);

      const locationForApi: Location = {
          id: selectedLocation.id,
          name: selectedLocation.name,
          prefecture: selectedLocation.prefecture,
          region: selectedLocation.region,
      };

      try {
        const result = await apiGenerateComment(locationForApi, { llmProvider });
        const generatedComment: ApiGeneratedComment = {
          id: result.id || selectedLocation.id,
          comment: result.comment,
          location: result.location || selectedLocation,
          timestamp: result.timestamp || new Date().toISOString(),
          settings: result.settings || { llmProvider, location: selectedLocation },
          confidence: result.confidence ?? 1,
        };
        setSingleGeneratedComment(generatedComment);
      } catch (err: any) {
        console.error('Failed to generate single comment:', err);
        setSingleGeneratedComment({
          id: selectedLocation.id,
          comment: '',
          location: selectedLocation,
          timestamp: new Date().toISOString(),
          settings: { llmProvider, location: selectedLocation },
          confidence: 0,
          error: err.message || 'コメント生成に失敗しました。'
        });
      } finally {
        setAppLoading(false);
      }
    }
  };

  const handleCopyComment = (text: string) => {
    navigator.clipboard?.writeText(text);
  };

  const currentTime = new Date().toLocaleString('ja-JP', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  });

  useEffect(() => {
    setSingleGeneratedComment(null);
    setProcessedComments([]);
    setAppError(null);
    if (!isBatchMode && getFallbackLocations().length > 0) {
      const defaultLocName = getFallbackLocations()[0];
      setSelectedLocation(getLocationInfo(defaultLocName));
    } else if (isBatchMode) {
      setSelectedLocation(null);
    }
  }, [isBatchMode]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Sun className="w-8 h-8 text-yellow-500 mr-3" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">天気コメント生成システム</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                React版 v1.0.1
              </span>
              <button onClick={toggleTheme} className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"><Moon className="w-5 h-5" /></button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center">
                  <Cloud className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" />
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">設定</h2>
                </div>
                <div className="p-6">
                  <GenerateSettingsComponent
                    llmProvider={llmProvider}
                    onLlmProviderChange={setLlmProvider}
                    isBatchMode={isBatchMode}
                    onBatchModeChange={setIsBatchMode}
                  />
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <LocationSelection
                  selectedLocation={selectedLocation}
                  selectedLocations={selectedLocations}
                  onLocationChange={setSelectedLocation}
                  onLocationsChange={setSelectedLocations}
                  isBatchMode={isBatchMode}
                  maxSelections={MAX_BATCH_LOCATIONS}
                />
              </div>

              {isBatchMode && selectedLocations.length >= WARN_BATCH_LOCATIONS && (
                <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 flex items-start">
                  <AlertTriangle className="w-5 h-5 mr-2 mt-0.5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-yellow-800 dark:text-yellow-200">大量の地点選択 ({selectedLocations.length}地点)</div>
                    <div className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">処理に時間がかかる可能性があります。最大{MAX_BATCH_LOCATIONS}地点。</div>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4 flex items-center text-blue-700 dark:text-blue-300">
                <Info className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="text-sm font-medium">生成時刻: {currentTime}</span>
              </div>

              <button
                type="button"
                onClick={handleGenerateComment}
                disabled={ (isBatchMode && selectedLocations.length === 0) || (!isBatchMode && !selectedLocation) || appLoading }
                className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {appLoading ? (
                  <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /><span>生成中...</span></>
                ) : (
                  <><Sparkles className="w-5 h-5" /><span>{isBatchMode ? `一括コメント生成 (${selectedLocations.length}地点)` : 'コメント生成'}</span></>
                )}
              </button>

              {appError && (
                <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4">
                  <p className="text-red-800 dark:text-red-200 text-sm">{appError}</p>
                </div>
              )}
            </div>

            <div className="lg:col-span-2 space-y-6">
              {appLoading && processedComments.length === 0 && !singleGeneratedComment && !isBatchMode && (
                <div className="text-center py-12"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-gray-600 dark:text-gray-300">コメントを生成しています...</p></div>
              )}
              {appLoading && isBatchMode && (processedComments.length === 0 || processedComments.every(p => p.status === 'pending')) && (
                 <div className="text-center py-12"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-gray-600 dark:text-gray-300">{selectedLocations.length} 地点のコメントを一括生成中です...</p></div>
              )}

              {isBatchMode && processedComments.length > 0 && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center mb-2"><Sparkles className="w-5 h-5 mr-2 text-gray-600 dark:text-gray-400" /><h2 className="text-lg font-semibold text-gray-900 dark:text-white">一括生成結果</h2></div>
                  <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/50 rounded-lg border border-blue-200 dark:border-blue-700">
                    <div className="text-sm text-blue-700 dark:text-blue-300">処理完了: {processedComments.filter(r => r.status === 'success' || r.status === 'error').length} / {processedComments.length} 地点</div>
                    <div className="text-sm text-green-700 dark:text-green-400">成功: {processedComments.filter(r => r.status === 'success').length} 件</div>
                    {processedComments.filter(r => r.status === 'error').length > 0 && (<div className="text-sm text-red-700 dark:text-red-400">失敗: {processedComments.filter(r => r.status === 'error').length} 件</div>)}
                    {processedComments.length > 0 && (<div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mt-2"><div className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out" style={{ width: `${(processedComments.filter(r => r.status === 'success' || r.status === 'error').length / processedComments.length) * 100}%` }}></div></div>)}
                  </div>
                  
                  {batchErrors.length > 0 && !appLoading && (
                    <div className="mt-4 mb-4 p-3 border border-red-300 bg-red-50 dark:bg-red-900/30 rounded-lg">
                      <h4 className="text-sm font-semibold text-red-700 dark:text-red-300 mb-1 flex items-center"><AlertTriangle className="w-4 h-4 mr-1.5"/>エラーが発生した地点:</h4>
                      <ul className="list-disc list-inside space-y-0.5 pl-4">
                        {batchErrors.map((item) => (<li key={`err-${item.id}`} className="text-xs text-red-600 dark:text-red-400"><strong>{item.locationName}:</strong> {item.error}</li>))}
                      </ul>
                    </div>
                  )}

                  <div className="space-y-3">
                    {processedComments.map((item) => (
                      <div key={item.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-3 shadow-sm">
                        {item.status === 'pending' && (<div className="flex items-center text-gray-500 dark:text-gray-400 text-sm"><Info className="w-4 h-4 mr-2 animate-pulse" /><span>{item.locationName} - 生成待機中...</span></div>)}
                        {item.status === 'generating' && (<div className="flex items-center text-blue-500 dark:text-blue-400 text-sm"><div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2" /><span>{item.locationName} - 生成中...</span></div>)}
                        {item.status === 'success' && item.comment && (
                          <div>
                            <div className="flex items-center text-green-700 dark:text-green-400 mb-1 text-sm font-medium"><CheckCircle2 className="w-4 h-4 mr-1.5" />{item.locationName} - 生成完了</div>
                            <p className="text-gray-800 dark:text-gray-200 text-sm bg-green-50 dark:bg-green-900/30 p-2 rounded">{item.comment}</p>
                            {item.metadata && (<details className="text-xs mt-1"><summary className="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">詳細情報</summary><pre className="mt-1 p-2 bg-gray-100 dark:bg-gray-700 rounded text-gray-700 dark:text-gray-300 text-xs overflow-x-auto">{JSON.stringify(item.metadata, null, 2)}</pre></details>)}
                            <button onClick={() => item.comment && handleCopyComment(item.comment)} className="mt-2 text-xs text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center"><CopyIcon size={12} className="mr-1"/>コピー</button>
                          </div>
                        )}
                        {item.status === 'error' && (
                           <div className="text-red-600 dark:text-red-400 text-sm">
                             <div className="flex items-center font-medium mb-0.5"><AlertTriangle className="w-4 h-4 mr-1.5" />{item.locationName} - 生成失敗</div>
                             <p className="text-xs ml-1 pl-4 border-l border-red-300 dark:border-red-700">{item.error}</p>
                           </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!isBatchMode && singleGeneratedComment && (
                <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  {singleGeneratedComment.error ? (
                     <div className="text-red-600 dark:text-red-400">
                       <h3 className="font-semibold mb-1">{singleGeneratedComment.location.name} - 生成失敗</h3>
                       <p className="text-sm">{singleGeneratedComment.error}</p>
                     </div>
                  ) : ( <GeneratedCommentDisplay comment={singleGeneratedComment as SharedGeneratedComment} onCopy={handleCopyComment}/> )}
                </div>
              )}

              {!appLoading && !singleGeneratedComment && processedComments.length === 0 && (
                 <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <div className="text-center py-12"><Sparkles className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" /><p className="text-gray-500 dark:text-gray-400">左のパネルから設定を選択し、コメントを生成してください。</p></div>
                 </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
