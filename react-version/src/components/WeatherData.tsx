import React from 'react';
import { Cloud, Thermometer, Droplets, Wind, Gauge, TrendingUp } from 'lucide-react';
import type { WeatherData } from '@mobile-comment-generator/shared';

interface WeatherDataProps {
  weather: WeatherData | null | any;
  metadata?: any;
  className?: string;
}

export const WeatherDataDisplay: React.FC<WeatherDataProps> = ({
  weather,
  className = '',
}) => {
  if (!weather) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <Cloud className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">天気データを取得中...</p>
      </div>
    );
  }

  const { current, forecast, trend } = weather;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 現在の天気 */}
      <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Cloud className="w-5 h-5 mr-2 text-blue-600" />
          現在の天気
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Thermometer className="w-5 h-5 text-red-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.temperature}°C</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">気温</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Droplets className="w-5 h-5 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.humidity}%</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">湿度</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Wind className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.windSpeed}m/s</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">風速</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <Gauge className="w-5 h-5 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{current.pressure}hPa</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">気圧</div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{current.icon}</span>
            <div>
              <div className="font-medium text-gray-900 dark:text-gray-100">{current.description}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">風向: {current.windDirection}</div>
            </div>
          </div>
        </div>
      </div>

      {/* 予報データ */}
      {forecast && forecast.length > 0 && (
        <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">天気予報</h3>
          
          <div className="space-y-3">
            {forecast.slice(0, 5).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">{item.icon}</span>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {new Date(item.datetime).toLocaleDateString('ja-JP', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">{item.description}</div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="font-bold text-gray-900 dark:text-gray-100">
                    {item.temperature.max}°C / {item.temperature.min}°C
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    湿度: {item.humidity}% | 降水: {item.precipitation}mm
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* トレンド情報 */}
      {trend && (
        <div className="bg-app-surface border border-app-border rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
            天気の傾向
          </h3>
          
          <div className="flex items-center space-x-4">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              trend.trend === 'improving' ? 'bg-green-100 text-green-800' :
              trend.trend === 'worsening' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {trend.trend === 'improving' ? '改善傾向' :
               trend.trend === 'worsening' ? '悪化傾向' : '安定'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              信頼度: {Math.round(trend.confidence * 100)}%
            </div>
          </div>

          <p className="mt-3 text-gray-700 dark:text-gray-300">{trend.description}</p>
        </div>
      )}
    </div>
  );
};