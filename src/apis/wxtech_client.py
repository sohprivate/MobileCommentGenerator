"""
WxTech API クライアント

Weathernews WxTech API との通信を行うクライアントクラス
"""

from typing import Dict, Any, List, Optional, Tuple
import requests
import json
import time
import warnings
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

from src.data.weather_data import (
    WeatherForecast, 
    WeatherForecastCollection,
    WeatherCondition,
    WindDirection
)
from src.data.location_manager import Location


class WxTechAPIError(Exception):
    """WxTech API エラー"""
    pass


class WxTechAPIClient:
    """WxTech API クライアント
    
    天気予報データの取得・処理を行う
    """
    
    # API設定
    BASE_URL = "https://wxtech.weathernews.com/openapi/v1"
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """クライアントを初期化
        
        Args:
            api_key: WxTech API キー
            timeout: タイムアウト秒数（デフォルト: 30秒）
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # ヘッダー設定
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "WxTechAPIClient/1.0"
        })
        
        # レート制限対策（秒間10リクエストまで）
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms
    
    def _rate_limit(self):
        """レート制限を適用"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """API リクエストを実行
        
        Args:
            endpoint: エンドポイント名
            params: リクエストパラメータ
            
        Returns:
            レスポンスデータ
            
        Raises:
            WxTechAPIError: API エラー
        """
        # レート制限
        self._rate_limit()
        
        # API キーをパラメータに追加
        params["apikey"] = self.api_key
        
        # URL 構築
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            # リクエスト実行
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # ステータスコードチェック
            if response.status_code == 401:
                raise WxTechAPIError("APIキーが無効です")
            elif response.status_code == 403:
                raise WxTechAPIError("APIアクセスが拒否されました")
            elif response.status_code == 404:
                raise WxTechAPIError("指定された地点データが見つかりません")
            elif response.status_code == 429:
                raise WxTechAPIError("レート制限に達しました")
            elif response.status_code == 500:
                raise WxTechAPIError("APIサーバーエラーが発生しました")
            elif response.status_code != 200:
                raise WxTechAPIError(
                    f"APIエラー: ステータスコード {response.status_code}"
                )
            
            # JSON パース
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise WxTechAPIError("レスポンスのJSONパースに失敗しました")
            
            # エラーレスポンスチェック
            if "error" in data:
                error_msg = data.get("message", "不明なエラー")
                raise WxTechAPIError(f"APIエラー: {error_msg}")
            
            # 成功レスポンス検証
            if "wxdata" not in data or not data["wxdata"]:
                raise WxTechAPIError("天気データが含まれていません")
            
            return data
            
        except requests.exceptions.Timeout:
            raise WxTechAPIError(f"リクエストがタイムアウトしました（{self.timeout}秒）")
        except requests.exceptions.ConnectionError:
            raise WxTechAPIError("API サーバーに接続できません")
        except requests.exceptions.RequestException as e:
            raise WxTechAPIError(f"リクエスト実行エラー: {str(e)}")
    
    def get_forecast(self, lat: float, lon: float) -> WeatherForecastCollection:
        """指定座標の天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            天気予報コレクション
            
        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        # パラメータ検証
        if not (-90 <= lat <= 90):
            raise ValueError(f"緯度が範囲外です: {lat} （-90～90の範囲で指定してください）")
        if not (-180 <= lon <= 180):
            raise ValueError(f"経度が範囲外です: {lon} （-180～180の範囲で指定してください）")
        
        # API リクエスト実行
        params = {
            "lat": lat,
            "lon": lon
        }
        
        raw_data = self._make_request("ss1wx", params)
        
        # レスポンスデータの変換
        return self._parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")
    
    def get_forecast_by_location(self, location: Location) -> WeatherForecastCollection:
        """Location オブジェクトから天気予報を取得
        
        Args:
            location: 地点情報
            
        Returns:
            天気予報コレクション
            
        Raises:
            ValueError: 地点に緯度経度情報がない場合
            WxTechAPIError: API エラーが発生した場合
        """
        if location.latitude is None or location.longitude is None:
            raise ValueError(f"地点 '{location.name}' に緯度経度情報がありません")
        
        forecast_collection = self.get_forecast(location.latitude, location.longitude)
        
        # 地点名を正しく設定
        forecast_collection.location = location.name
        for forecast in forecast_collection.forecasts:
            forecast.location = location.name
        
        return forecast_collection
    
    async def get_forecast_async(self, lat: float, lon: float) -> WeatherForecastCollection:
        """非同期で天気予報を取得
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            天気予報コレクション
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(
                pool, 
                self.get_forecast, 
                lat, 
                lon
            )
    
    def _parse_forecast_response(
        self, 
        raw_data: Dict[str, Any], 
        location_name: str
    ) -> WeatherForecastCollection:
        """API レスポンスを WeatherForecastCollection に変換
        
        Args:
            raw_data: API からの生データ
            location_name: 地点名
            
        Returns:
            天気予報コレクション
        """
        wxdata = raw_data["wxdata"][0]
        forecasts = []
        
        # 短期予報（時間別）の処理
        if "srf" in wxdata:
            for forecast_data in wxdata["srf"]:
                try:
                    forecast = self._parse_single_forecast(
                        forecast_data, 
                        location_name, 
                        is_hourly=True
                    )
                    forecasts.append(forecast)
                except Exception as e:
                    warnings.warn(f"時間別予報の解析に失敗: {str(e)}")
                    continue
        
        # 中期予報（日別）の処理
        if "mrf" in wxdata:
            for forecast_data in wxdata["mrf"]:
                try:
                    forecast = self._parse_single_forecast(
                        forecast_data, 
                        location_name, 
                        is_hourly=False
                    )
                    forecasts.append(forecast)
                except Exception as e:
                    warnings.warn(f"日別予報の解析に失敗: {str(e)}")
                    continue
        
        return WeatherForecastCollection(
            location=location_name,
            forecasts=forecasts
        )
    
    def _parse_single_forecast(
        self, 
        data: Dict[str, Any], 
        location_name: str, 
        is_hourly: bool = True
    ) -> WeatherForecast:
        """単一の予報データを WeatherForecast に変換
        
        Args:
            data: 予報データ
            location_name: 地点名
            is_hourly: 時間別予報かどうか
            
        Returns:
            天気予報オブジェクト
        """
        # 日時の解析
        date_str = data["date"]
        forecast_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        # 天気コードの変換
        weather_code = str(data["wx"])
        weather_condition = self._convert_weather_code(weather_code)
        weather_description = self._get_weather_description(weather_code)
        
        # 風向きの変換
        wind_dir_index = data.get("wnddir", 0)
        wind_direction, wind_degrees = self._convert_wind_direction(wind_dir_index)
        
        # 気温の取得（時間別と日別で異なるフィールド）
        if is_hourly:
            temperature = float(data["temp"])
        else:
            # 日別予報の場合は最高気温を使用
            temperature = float(data.get("maxtemp", data.get("temp", 0)))
        
        return WeatherForecast(
            location=location_name,
            datetime=forecast_datetime,
            temperature=temperature,
            weather_code=weather_code,
            weather_condition=weather_condition,
            weather_description=weather_description,
            precipitation=float(data.get("prec", 0)),
            humidity=float(data.get("rhum", 0)),
            wind_speed=float(data.get("wndspd", 0)),
            wind_direction=wind_direction,
            wind_direction_degrees=wind_degrees,
            raw_data=data
        )
    
    def _convert_weather_code(self, weather_code: str) -> WeatherCondition:
        """WxTech天気コードを標準的な天気状況に変換
        
        Args:
            weather_code: WxTech API の天気コード
            
        Returns:
            標準化された天気状況
        """
        # WxTech APIの天気コードマッピング（例）
        # 実際のマッピングは既存の translate_weather_code.py を参照
        code_mapping = {
            "100": WeatherCondition.CLEAR,
            "101": WeatherCondition.CLEAR,
            "110": WeatherCondition.PARTLY_CLOUDY,
            "111": WeatherCondition.PARTLY_CLOUDY,
            "200": WeatherCondition.CLOUDY,
            "201": WeatherCondition.CLOUDY,
            "300": WeatherCondition.RAIN,
            "301": WeatherCondition.RAIN,
            "302": WeatherCondition.HEAVY_RAIN,
            "400": WeatherCondition.SNOW,
            "401": WeatherCondition.SNOW,
            "402": WeatherCondition.HEAVY_SNOW,
            "500": WeatherCondition.STORM,
        }
        
        return code_mapping.get(weather_code, WeatherCondition.UNKNOWN)
    
    def _get_weather_description(self, weather_code: str) -> str:
        """天気コードから日本語説明を取得
        
        Args:
            weather_code: WxTech API の天気コード
            
        Returns:
            日本語の天気説明
        """
        # 実際の実装では既存の translate_weather_code.py を使用
        descriptions = {
            "100": "晴れ",
            "101": "快晴",
            "110": "晴れ時々曇り",
            "111": "晴れのち曇り",
            "200": "曇り",
            "201": "薄曇り",
            "300": "雨",
            "301": "小雨",
            "302": "大雨",
            "400": "雪",
            "401": "小雪",
            "402": "大雪",
            "500": "嵐",
        }
        
        return descriptions.get(weather_code, "不明")
    
    def _convert_wind_direction(self, wind_dir_index: int) -> tuple[WindDirection, int]:
        """風向きインデックスを風向きと度数に変換
        
        Args:
            wind_dir_index: WxTech API の風向きインデックス
            
        Returns:
            (風向き, 度数) のタプル
        """
        # 実際の実装では既存の translate_wind_direction2degrees.py を使用
        direction_mapping = {
            0: (WindDirection.CALM, 0),
            1: (WindDirection.N, 0),
            2: (WindDirection.NE, 45),
            3: (WindDirection.E, 90),
            4: (WindDirection.SE, 135),
            5: (WindDirection.S, 180),
            6: (WindDirection.SW, 225),
            7: (WindDirection.W, 270),
            8: (WindDirection.NW, 315),
        }
        
        return direction_mapping.get(wind_dir_index, (WindDirection.UNKNOWN, 0))
    
    def close(self):
        """セッションを閉じる"""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 既存の関数との互換性を保つためのラッパー関数
async def get_japan_1km_mesh_weather_forecast(
    lat: float, 
    lon: float, 
    api_key: str
) -> Dict[str, Any]:
    """既存の get_japan_1km_mesh_weather_forecast 関数の互換ラッパー
    
    Args:
        lat: 緯度
        lon: 経度
        api_key: WxTech API キー
        
    Returns:
        天気予報データの辞書
    """
    client = WxTechAPIClient(api_key)
    try:
        forecast_collection = await client.get_forecast_async(lat, lon)
        return forecast_collection.to_dict()
    finally:
        client.close()