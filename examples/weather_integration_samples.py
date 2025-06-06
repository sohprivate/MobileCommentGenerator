"""
天気予報統合機能のサンプル実装

このファイルは、Issue #3 で実装された天気予報統合機能の
実際の使用例を示すサンプル集です。
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# 天気予報機能のインポート
from src.apis.wxtech_client import WxTechAPIClient
from src.data.location_manager import get_location_manager
from src.nodes.weather_forecast_node import (
    WeatherForecastNode,
    get_weather_forecast_for_location,
    integrate_weather_into_conversation
)
from src.config.weather_config import get_config, setup_environment_defaults

# 環境変数をロード
load_dotenv()


class WeatherIntegrationSamples:
    """天気予報統合のサンプル実装クラス"""
    
    def __init__(self):
        """サンプル実装クラスを初期化"""
        setup_environment_defaults()
        self.config = get_config()
        self.location_manager = get_location_manager()
        
        if not self.config.weather.wxtech_api_key:
            raise ValueError("WXTECH_API_KEY環境変数を設定してください")
    
    async def sample_basic_weather_forecast(self):
        """基本的な天気予報取得のサンプル"""
        print("=== 基本的な天気予報取得 ===")
        
        try:
            with WxTechAPIClient(self.config.weather.wxtech_api_key) as client:
                # 東京の天気予報を取得
                forecast_collection = client.get_forecast(35.6762, 139.6503)
                
                print(f"地点: {forecast_collection.location}")
                print(f"予報データ数: {len(forecast_collection.forecasts)}")
                
                # 現在の予報
                current_forecast = forecast_collection.get_current_forecast()
                if current_forecast:
                    print(f"現在の天気: {current_forecast.weather_description}")
                    print(f"気温: {current_forecast.temperature}°C")
                    print(f"湿度: {current_forecast.humidity}%")
                    print(f"風速: {current_forecast.wind_speed}m/s")
                    print(f"降水量: {current_forecast.precipitation}mm")
                    print(f"快適度: {current_forecast.get_comfort_level()}")
                
                # 日次サマリー
                summary = forecast_collection.get_daily_summary()
                print(f"\n日次サマリー:")
                print(f"  最高気温: {summary['max_temperature']}°C")
                print(f"  最低気温: {summary['min_temperature']}°C")
                print(f"  平均気温: {summary['avg_temperature']:.1f}°C")
                print(f"  総降水量: {summary['total_precipitation']}mm")
                
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_location_based_forecast(self):
        """地点名による天気予報取得のサンプル"""
        print("\n=== 地点名による天気予報取得 ===")
        
        locations = ["東京", "大阪", "札幌", "福岡", "那覇"]
        
        try:
            with WxTechAPIClient(self.config.weather.wxtech_api_key) as client:
                for location_name in locations:
                    location = self.location_manager.get_location(location_name)
                    if location:
                        forecast_collection = client.get_forecast_by_location(location)
                        current = forecast_collection.get_current_forecast()
                        
                        if current:
                            print(f"{location_name}: {current.weather_description}, "
                                  f"{current.temperature}°C, "
                                  f"降水量{current.precipitation}mm")
                        
                        # 少し待機（レート制限対策）
                        await asyncio.sleep(0.2)
                    else:
                        print(f"{location_name}: 地点が見つかりません")
                        
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_weather_node_integration(self):
        """LangGraphノードとしての天気予報統合サンプル"""
        print("\n=== LangGraphノード統合 ===")
        
        try:
            # 複数地点の天気情報を取得
            locations = ["東京", "横浜", "千葉"]
            
            for location in locations:
                result = await get_weather_forecast_for_location(
                    location=location,
                    api_key=self.config.weather.wxtech_api_key,
                    forecast_hours=12
                )
                
                if result.get('error_message'):
                    print(f"{location}: {result['error_message']}")
                    continue
                
                weather_summary = result['weather_summary']
                current_weather = weather_summary['current_weather']
                recommendations = weather_summary.get('recommendations', [])
                
                print(f"\n{location}の天気情報:")
                print(f"  天気: {current_weather['description']}")
                print(f"  気温: {current_weather['temperature']}°C")
                print(f"  快適度: {current_weather['comfort_level']}")
                
                if recommendations:
                    print("  推奨事項:")
                    for rec in recommendations[:3]:  # 最大3つまで表示
                        print(f"    - {rec}")
                
                await asyncio.sleep(0.2)
                
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_conversation_integration(self):
        """会話への天気情報統合サンプル"""
        print("\n=== 会話への天気情報統合 ===")
        
        try:
            # サンプル会話メッセージ
            sample_conversations = [
                [HumanMessage(content="今日の外出の予定について相談したいです")],
                [HumanMessage(content="明日のピクニックは大丈夫でしょうか？")],
                [HumanMessage(content="洗濯物を外に干そうと思っているのですが")]
            ]
            
            for i, messages in enumerate(sample_conversations, 1):
                print(f"\n--- 会話例 {i} ---")
                print(f"ユーザー: {messages[0].content}")
                
                # 天気情報を統合
                enhanced_messages = await integrate_weather_into_conversation(
                    messages=messages,
                    location="東京",
                    api_key=self.config.weather.wxtech_api_key
                )
                
                # 天気情報メッセージを表示
                if len(enhanced_messages) > len(messages):
                    weather_message = enhanced_messages[-1]
                    print(f"システム（天気情報）:")
                    print(weather_message.content)
                
                await asyncio.sleep(0.3)
                
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_custom_location_management(self):
        """カスタム地点管理のサンプル"""
        print("\n=== カスタム地点管理 ===")
        
        try:
            # カスタム地点の追加
            from src.data.location_manager import Location
            
            custom_locations = [
                Location("幕張", "千葉県", 35.6490, 140.0347),
                Location("みなとみらい", "神奈川県", 35.4593, 139.6380),
                Location("お台場", "東京都", 35.6269, 139.7744)
            ]
            
            for location in custom_locations:
                self.location_manager.add_location(location)
                print(f"地点追加: {location.name} ({location.prefecture})")
            
            # 追加した地点の天気を取得
            print("\nカスタム地点の天気予報:")
            
            with WxTechAPIClient(self.config.weather.wxtech_api_key) as client:
                for location in custom_locations:
                    forecast_collection = client.get_forecast_by_location(location)
                    current = forecast_collection.get_current_forecast()
                    
                    if current:
                        print(f"{location.name}: {current.weather_description}, "
                              f"{current.temperature}°C")
                    
                    await asyncio.sleep(0.2)
            
            # 地点検索のテスト
            print("\n地点検索テスト:")
            search_results = self.location_manager.search_locations("みなと")
            for result in search_results[:3]:
                print(f"  {result.name} ({result.prefecture})")
                
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_advanced_weather_analysis(self):
        """高度な天気分析のサンプル"""
        print("\n=== 高度な天気分析 ===")
        
        try:
            # 24時間の詳細予報を取得
            result = await get_weather_forecast_for_location(
                location="東京",
                api_key=self.config.weather.wxtech_api_key,
                forecast_hours=24
            )
            
            if result.get('error_message'):
                print(f"エラー: {result['error_message']}")
                return
            
            weather_data = result['weather_data']
            forecasts = weather_data['forecasts']
            
            # 時間別分析
            print("24時間予報分析:")
            print(f"予報データ数: {len(forecasts)}")
            
            # 雨の時間帯を特定
            rainy_hours = []
            for forecast in forecasts:
                if forecast['precipitation'] > 0.1:
                    dt = datetime.fromisoformat(forecast['datetime'])
                    rainy_hours.append((dt.hour, forecast['precipitation']))
            
            if rainy_hours:
                print("雨の予報がある時間帯:")
                for hour, precipitation in rainy_hours:
                    print(f"  {hour:02d}時: {precipitation}mm")
            else:
                print("24時間以内に雨の予報はありません")
            
            # 気温変化の分析
            temperatures = [(datetime.fromisoformat(f['datetime']).hour, f['temperature']) 
                          for f in forecasts]
            
            if len(temperatures) >= 2:
                max_temp_hour, max_temp = max(temperatures, key=lambda x: x[1])
                min_temp_hour, min_temp = min(temperatures, key=lambda x: x[1])
                
                print(f"\n気温変化:")
                print(f"  最高気温: {max_temp}°C ({max_temp_hour:02d}時頃)")
                print(f"  最低気温: {min_temp}°C ({min_temp_hour:02d}時頃)")
                print(f"  日較差: {max_temp - min_temp:.1f}°C")
            
            # アラート生成
            alerts = result['weather_summary']['alerts']
            if any(alerts.values()):
                print("\n気象アラート:")
                if alerts.get('has_severe_weather'):
                    print("  ⚠️ 悪天候の予報があります")
                if alerts.get('high_precipitation'):
                    print("  ☔ 強い雨の予報があります")
                if alerts.get('extreme_temperature'):
                    print("  🌡️ 極端な気温の予報があります")
            else:
                print("\n特別な気象警告はありません")
                
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    async def sample_parallel_weather_requests(self):
        """並列天気リクエストのサンプル"""
        print("\n=== 並列天気予報取得 ===")
        
        try:
            # 複数地点の天気を並列取得
            major_cities = ["東京", "大阪", "名古屋", "札幌", "福岡", "仙台"]
            
            print(f"{len(major_cities)}地点の天気予報を並列取得中...")
            
            # 並列タスクを作成
            tasks = [
                get_weather_forecast_for_location(
                    location=city,
                    api_key=self.config.weather.wxtech_api_key,
                    forecast_hours=6
                )
                for city in major_cities
            ]
            
            # 並列実行
            start_time = datetime.now()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            print(f"処理時間: {processing_time:.2f}秒")
            
            # 結果をまとめて表示
            print("\n全国天気概況:")
            for city, result in zip(major_cities, results):
                if isinstance(result, Exception):
                    print(f"{city}: エラー - {str(result)}")
                elif result.get('error_message'):
                    print(f"{city}: {result['error_message']}")
                else:
                    current = result['weather_summary']['current_weather']
                    comfort = current['comfort_level']
                    comfort_emoji = {"comfortable": "😊", "moderate": "😐", "uncomfortable": "😟"}
                    
                    print(f"{city}: {current['description']} {current['temperature']}°C "
                          f"{comfort_emoji.get(comfort, '?')}")
                          
        except Exception as e:
            print(f"エラー: {str(e)}")
    
    def sample_configuration_management(self):
        """設定管理のサンプル"""
        print("\n=== 設定管理 ===")
        
        try:
            # 現在の設定を表示
            print("現在の設定:")
            config_dict = self.config.to_dict()
            
            for category, settings in config_dict.items():
                print(f"\n{category}:")
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {settings}")
            
            # 設定検証
            from src.config.weather_config import validate_config
            
            validation_errors = validate_config(self.config)
            if validation_errors:
                print("\n設定検証エラー:")
                for category, errors in validation_errors.items():
                    print(f"{category}:")
                    for error in errors:
                        print(f"  - {error}")
            else:
                print("\n✅ 設定検証: 問題なし")
                
        except Exception as e:
            print(f"エラー: {str(e)}")


async def main():
    """メイン実行関数"""
    print("天気予報統合機能 サンプル実行")
    print("=" * 50)
    
    try:
        samples = WeatherIntegrationSamples()
        
        # 各サンプルを順次実行
        await samples.sample_basic_weather_forecast()
        await samples.sample_location_based_forecast()
        await samples.sample_weather_node_integration()
        await samples.sample_conversation_integration()
        await samples.sample_custom_location_management()
        await samples.sample_advanced_weather_analysis()
        await samples.sample_parallel_weather_requests()
        samples.sample_configuration_management()
        
    except ValueError as e:
        print(f"設定エラー: {str(e)}")
        print("\n.envファイルにWXTECH_API_KEYを設定してください:")
        print("WXTECH_API_KEY=your_api_key_here")
    except Exception as e:
        print(f"実行エラー: {str(e)}")
    
    print("\n" + "=" * 50)
    print("サンプル実行完了")


if __name__ == "__main__":
    # サンプル実行
    asyncio.run(main())
