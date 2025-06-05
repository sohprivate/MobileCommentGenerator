"""
WxTech API クライアント

Weathernews WxTech APIとの連携を行うクライアントクラス
既存の get_japan_1km_mesh_weather_forecast.py をベースに、
より堅牢で拡張可能な実装を提供
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import warnings

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.data.weather_data import (
    WeatherForecast, 
    WeatherForecastCollection, 
    WeatherCondition, 
    WindDirection
)
from src.data.location_manager import Location


class WxTechAPIError(Exception):
    """WxTech API関連のエラー"""
    pass


class WxTechAPIClient:
    """WxTech API クライアント
    
    Weathernews WxTech APIからの天気予報データ取得を行うクライアント
    """
    
    def __init__(
        self, 
        api_key: str,
        base_url: str = "https://wxtech.weathernews.com/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 0.1
    ):
        """WxTech APIクライアントを初期化
        
        Args:
            api_key: WxTech API キー
            base_url: API のベースURL
            timeout: リクエストタイムアウト（秒）
            max_retries: 最大リトライ回数
            rate_limit_delay: レート制限回避のための遅延（秒）
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        
        # セッションの設定（接続プーリング・リトライ戦略）
        self.session = requests.Session()
        
        # リトライ戦略の設定
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 共通ヘッダー
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "User-Agent": "MobileCommentGenerator/1.0"
        })
        
        # レート制限管理
        self.last_request_time = 0.0
    
    def _wait_for_rate_limit(self) -> None:
        """レート制限を考慮した待機処理"""
        if self.rate_limit_delay > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """API リクエストを実行
        
        Args:
            endpoint: API エンドポイント
            params: リクエストパラメータ
            
        Returns:
            API レスポンスデータ
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # HTTPステータスコードチェック
            if response.status_code == 401:
                raise WxTechAPIError("認証エラー: APIキーが無効です")
            elif response.status_code == 403:
                raise WxTechAPIError("アクセス拒否: APIキーに必要な権限がありません")
            elif response.status_code == 429:
                raise WxTechAPIError("レート制限に達しました")
            elif response.status_code == 404:
                raise WxTechAPIError("指定された地点の天気データが見つかりません")
            elif not response.ok:
                raise WxTechAPIError(f"API エラー: HTTP {response.status_code}")
            
            # JSON レスポンスの解析
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise WxTechAPIError(f"レスポンスのJSON解析に失敗: {str(e)}")
            
            # API固有のエラーチェック
            if not data.get("wxdata"):
                raise WxTechAPIError("天気データが含まれていません")
            
            return data
            
        except requests.exceptions.Timeout:
            raise WxTechAPIError(f"リクエストがタイムアウトしました（{self.timeout}秒）")\n        except requests.exceptions.ConnectionError:\n            raise WxTechAPIError(\"API サーバーに接続できません\")\n        except requests.exceptions.RequestException as e:\n            raise WxTechAPIError(f\"リクエスト実行エラー: {str(e)}\")\n    \n    def get_forecast(self, lat: float, lon: float) -> WeatherForecastCollection:\n        \"\"\"指定座標の天気予報を取得\n        \n        Args:\n            lat: 緯度\n            lon: 経度\n            \n        Returns:\n            天気予報コレクション\n            \n        Raises:\n            WxTechAPIError: API エラーが発生した場合\n        \"\"\"\n        # パラメータ検証\n        if not (-90 <= lat <= 90):\n            raise ValueError(f\"緯度が範囲外です: {lat} （-90～90の範囲で指定してください）\")\n        if not (-180 <= lon <= 180):\n            raise ValueError(f\"経度が範囲外です: {lon} （-180～180の範囲で指定してください）\")\n        \n        # API リクエスト実行\n        params = {\n            \"lat\": lat,\n            \"lon\": lon\n        }\n        \n        raw_data = self._make_request(\"ss1wx\", params)\n        \n        # レスポンスデータの変換\n        return self._parse_forecast_response(raw_data, f\"lat:{lat},lon:{lon}\")\n    \n    def get_forecast_by_location(self, location: Location) -> WeatherForecastCollection:\n        \"\"\"Location オブジェクトから天気予報を取得\n        \n        Args:\n            location: 地点情報\n            \n        Returns:\n            天気予報コレクション\n            \n        Raises:\n            ValueError: 地点に緯度経度情報がない場合\n            WxTechAPIError: API エラーが発生した場合\n        \"\"\"\n        if location.latitude is None or location.longitude is None:\n            raise ValueError(f\"地点 '{location.name}' に緯度経度情報がありません\")\n        \n        forecast_collection = self.get_forecast(location.latitude, location.longitude)\n        \n        # 地点名を正しく設定\n        forecast_collection.location = location.name\n        for forecast in forecast_collection.forecasts:\n            forecast.location = location.name\n        \n        return forecast_collection\n    \n    async def get_forecast_async(self, lat: float, lon: float) -> WeatherForecastCollection:\n        \"\"\"非同期で天気予報を取得\n        \n        Args:\n            lat: 緯度\n            lon: 経度\n            \n        Returns:\n            天気予報コレクション\n        \"\"\"\n        loop = asyncio.get_running_loop()\n        with ThreadPoolExecutor() as pool:\n            return await loop.run_in_executor(\n                pool, \n                self.get_forecast, \n                lat, \n                lon\n            )\n    \n    def _parse_forecast_response(\n        self, \n        raw_data: Dict[str, Any], \n        location_name: str\n    ) -> WeatherForecastCollection:\n        \"\"\"API レスポンスを WeatherForecastCollection に変換\n        \n        Args:\n            raw_data: API からの生データ\n            location_name: 地点名\n            \n        Returns:\n            天気予報コレクション\n        \"\"\"\n        wxdata = raw_data[\"wxdata\"][0]\n        forecasts = []\n        \n        # 短期予報（時間別）の処理\n        if \"srf\" in wxdata:\n            for forecast_data in wxdata[\"srf\"]:\n                try:\n                    forecast = self._parse_single_forecast(\n                        forecast_data, \n                        location_name, \n                        is_hourly=True\n                    )\n                    forecasts.append(forecast)\n                except Exception as e:\n                    warnings.warn(f\"時間別予報の解析に失敗: {str(e)}\")\n                    continue\n        \n        # 中期予報（日別）の処理\n        if \"mrf\" in wxdata:\n            for forecast_data in wxdata[\"mrf\"]:\n                try:\n                    forecast = self._parse_single_forecast(\n                        forecast_data, \n                        location_name, \n                        is_hourly=False\n                    )\n                    forecasts.append(forecast)\n                except Exception as e:\n                    warnings.warn(f\"日別予報の解析に失敗: {str(e)}\")\n                    continue\n        \n        return WeatherForecastCollection(\n            location=location_name,\n            forecasts=forecasts\n        )\n    \n    def _parse_single_forecast(\n        self, \n        data: Dict[str, Any], \n        location_name: str, \n        is_hourly: bool = True\n    ) -> WeatherForecast:\n        \"\"\"単一の予報データを WeatherForecast に変換\n        \n        Args:\n            data: 予報データ\n            location_name: 地点名\n            is_hourly: 時間別予報かどうか\n            \n        Returns:\n            天気予報オブジェクト\n        \"\"\"\n        # 日時の解析\n        date_str = data[\"date\"]\n        forecast_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))\n        \n        # 天気コードの変換\n        weather_code = str(data[\"wx\"])\n        weather_condition = self._convert_weather_code(weather_code)\n        weather_description = self._get_weather_description(weather_code)\n        \n        # 風向きの変換\n        wind_dir_index = data.get(\"wnddir\", 0)\n        wind_direction, wind_degrees = self._convert_wind_direction(wind_dir_index)\n        \n        # 気温の取得（時間別と日別で異なるフィールド）\n        if is_hourly:\n            temperature = float(data[\"temp\"])\n        else:\n            # 日別予報の場合は最高気温を使用\n            temperature = float(data.get(\"maxtemp\", data.get(\"temp\", 0)))\n        \n        return WeatherForecast(\n            location=location_name,\n            datetime=forecast_datetime,\n            temperature=temperature,\n            weather_code=weather_code,\n            weather_condition=weather_condition,\n            weather_description=weather_description,\n            precipitation=float(data.get(\"prec\", 0)),\n            humidity=float(data.get(\"rhum\", 0)),\n            wind_speed=float(data.get(\"wndspd\", 0)),\n            wind_direction=wind_direction,\n            wind_direction_degrees=wind_degrees,\n            raw_data=data\n        )\n    \n    def _convert_weather_code(self, weather_code: str) -> WeatherCondition:\n        \"\"\"WxTech天気コードを標準的な天気状況に変換\n        \n        Args:\n            weather_code: WxTech API の天気コード\n            \n        Returns:\n            標準化された天気状況\n        \"\"\"\n        # WxTech APIの天気コードマッピング（例）\n        # 実際のマッピングは既存の translate_weather_code.py を参照\n        code_mapping = {\n            \"100\": WeatherCondition.CLEAR,\n            \"101\": WeatherCondition.CLEAR,\n            \"110\": WeatherCondition.PARTLY_CLOUDY,\n            \"111\": WeatherCondition.PARTLY_CLOUDY,\n            \"200\": WeatherCondition.CLOUDY,\n            \"201\": WeatherCondition.CLOUDY,\n            \"300\": WeatherCondition.RAIN,\n            \"301\": WeatherCondition.RAIN,\n            \"302\": WeatherCondition.HEAVY_RAIN,\n            \"400\": WeatherCondition.SNOW,\n            \"401\": WeatherCondition.SNOW,\n            \"402\": WeatherCondition.HEAVY_SNOW,\n            \"500\": WeatherCondition.STORM,\n        }\n        \n        return code_mapping.get(weather_code, WeatherCondition.UNKNOWN)\n    \n    def _get_weather_description(self, weather_code: str) -> str:\n        \"\"\"天気コードから日本語説明を取得\n        \n        Args:\n            weather_code: WxTech API の天気コード\n            \n        Returns:\n            日本語の天気説明\n        \"\"\"\n        # 実際の実装では既存の translate_weather_code.py を使用\n        descriptions = {\n            \"100\": \"晴れ\",\n            \"101\": \"快晴\",\n            \"110\": \"晴れ時々曇り\",\n            \"111\": \"晴れのち曇り\",\n            \"200\": \"曇り\",\n            \"201\": \"薄曇り\",\n            \"300\": \"雨\",\n            \"301\": \"小雨\",\n            \"302\": \"大雨\",\n            \"400\": \"雪\",\n            \"401\": \"小雪\",\n            \"402\": \"大雪\",\n            \"500\": \"嵐\",\n        }\n        \n        return descriptions.get(weather_code, \"不明\")\n    \n    def _convert_wind_direction(self, wind_dir_index: int) -> tuple[WindDirection, int]:\n        \"\"\"風向きインデックスを風向きと度数に変換\n        \n        Args:\n            wind_dir_index: WxTech API の風向きインデックス\n            \n        Returns:\n            (風向き, 度数) のタプル\n        \"\"\"\n        # 実際の実装では既存の translate_wind_direction2degrees.py を使用\n        direction_mapping = {\n            0: (WindDirection.CALM, 0),\n            1: (WindDirection.N, 0),\n            2: (WindDirection.NE, 45),\n            3: (WindDirection.E, 90),\n            4: (WindDirection.SE, 135),\n            5: (WindDirection.S, 180),\n            6: (WindDirection.SW, 225),\n            7: (WindDirection.W, 270),\n            8: (WindDirection.NW, 315),\n        }\n        \n        return direction_mapping.get(wind_dir_index, (WindDirection.UNKNOWN, 0))\n    \n    def close(self):\n        \"\"\"セッションを閉じる\"\"\"\n        if hasattr(self, 'session'):\n            self.session.close()\n    \n    def __enter__(self):\n        return self\n    \n    def __exit__(self, exc_type, exc_val, exc_tb):\n        self.close()\n\n\n# 既存の関数との互換性を保つためのラッパー関数\nasync def get_japan_1km_mesh_weather_forecast(\n    lat: float, \n    lon: float, \n    api_key: str\n) -> Dict[str, Any]:\n    \"\"\"既存の get_japan_1km_mesh_weather_forecast 関数の互換ラッパー\n    \n    Args:\n        lat: 緯度\n        lon: 経度\n        api_key: WxTech API キー\n        \n    Returns:\n        天気予報データの辞書\n    \"\"\"\n    client = WxTechAPIClient(api_key)\n    try:\n        forecast_collection = await client.get_forecast_async(lat, lon)\n        return forecast_collection.to_dict()\n    finally:\n        client.close()\n"