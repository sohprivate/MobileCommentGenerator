"""
WxTech API クライアント

Weathernews WxTech API との通信を行うクライアントクラス
"""

import time
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor
import warnings

from src.data.weather_data import (
    WeatherForecast,
    WeatherForecastCollection,
    WeatherCondition,
    WindDirection,
)
from src.data.location_manager import Location


class WxTechAPIError(Exception):
    """WxTech API エラー
    
    Attributes:
        status_code: HTTPステータスコード（あれば）
        error_type: エラータイプ（api_key_invalid, rate_limit, network_error等）
    """
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_type: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


class WxTechAPIClient:
    """WxTech API クライアント

    天気予報データの取得・処理を行う
    """

    # API設定
    BASE_URL = "https://wxtech.weathernews.com/api/v1"
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
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "WxTechAPIClient/1.0",
                "X-API-Key": self.api_key,
            }
        )

        # レート制限対策（秒間10リクエストまで）
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms

    async def _rate_limit(self):
        """レート制限を適用（非同期版）"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
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
        await self._rate_limit()

        # URL 構築
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            # リクエスト実行
            response = self.session.get(url, params=params, timeout=self.timeout)

            # ステータスコードチェック
            if response.status_code == 401:
                raise WxTechAPIError("APIキーが無効です", status_code=401, error_type='api_key_invalid')
            elif response.status_code == 403:
                raise WxTechAPIError("APIアクセスが拒否されました", status_code=403, error_type='http_error')
            elif response.status_code == 404:
                raise WxTechAPIError("指定された地点データが見つかりません", status_code=404, error_type='http_error')
            elif response.status_code == 429:
                raise WxTechAPIError("レート制限に達しました", status_code=429, error_type='rate_limit')
            elif response.status_code == 500:
                raise WxTechAPIError("APIサーバーエラーが発生しました", status_code=500, error_type='server_error')
            elif response.status_code != 200:
                raise WxTechAPIError(f"APIエラー: ステータスコード {response.status_code}", status_code=response.status_code, error_type='http_error')

            # JSON パース
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise WxTechAPIError("レスポンスのJSONパースに失敗しました", status_code=response.status_code, error_type='http_error')

            # エラーレスポンスチェック
            if "error" in data:
                error_msg = data.get("message", "不明なエラー")
                raise WxTechAPIError(f"APIエラー: {error_msg}", status_code=response.status_code, error_type='http_error')

            # 成功レスポンス検証
            if "wxdata" not in data or not data["wxdata"]:
                raise WxTechAPIError("天気データが含まれていません", status_code=response.status_code, error_type='http_error')

            return data

        except requests.exceptions.Timeout:
            raise WxTechAPIError(f"リクエストがタイムアウトしました（{self.timeout}秒）", error_type='timeout')
        except requests.exceptions.ConnectionError:
            raise WxTechAPIError("API サーバーに接続できません", error_type='network_error')
        except requests.exceptions.RequestException as e:
            raise WxTechAPIError(f"リクエスト実行エラー: {str(e)}", error_type='network_error')

    async def get_forecast(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """指定座標の天気予報を取得

        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）

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
        if forecast_hours <= 0 or forecast_hours > 168:  # 最大7日間
            raise ValueError(f"予報時間数が範囲外です: {forecast_hours} （1-168時間の範囲で指定してください）")

        # API リクエスト実行（72時間の予報データを要求）
        params = {
            "lat": lat, 
            "lon": lon,
            "hours": forecast_hours  # 予報時間数パラメータ
        }

        # ログ出力でパラメータを確認
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 WxTech API リクエスト: endpoint=ss1wx, params={params}")
        
        raw_data = await self._make_request("ss1wx", params)
        
        # レスポンスの基本情報をログ出力
        if "wxdata" in raw_data and raw_data["wxdata"]:
            wxdata = raw_data["wxdata"][0]
            srf_count = len(wxdata.get("srf", []))
            mrf_count = len(wxdata.get("mrf", []))
            logger.info(f"📊 WxTech API レスポンス: srf={srf_count}件, mrf={mrf_count}件")

        # レスポンスデータの変換
        return self._parse_forecast_response(raw_data, f"lat:{lat},lon:{lon}")

    async def get_forecast_by_location(self, location: Location) -> WeatherForecastCollection:
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

        forecast_collection = await self.get_forecast_for_next_day_hours(location.latitude, location.longitude)

        # 地点名を正しく設定
        forecast_collection.location = location.name
        for forecast in forecast_collection.forecasts:
            forecast.location = location.name

        return forecast_collection

    async def get_forecast_for_next_day_hours(self, lat: float, lon: float) -> WeatherForecastCollection:
        """翌日の9, 12, 15, 18時JSTの最も近い時刻のデータのみを取得

        Args:
            lat: 緯度
            lon: 経度

        Returns:
            翌日の最も近い時刻の天気予報コレクション

        Raises:
            WxTechAPIError: API エラーが発生した場合
        """
        import pytz
        from datetime import timedelta, datetime as dt
        import logging
        
        logger = logging.getLogger(__name__)
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = dt.now(jst)
        
        # 翌日の日付
        target_date = now_jst.date() + timedelta(days=1)
        
        # 翌日の9, 12, 15, 18時JSTの時刻を作成
        target_hours = [9, 12, 15, 18]
        target_times = []
        for hour in target_hours:
            target_dt = jst.localize(dt.combine(target_date, dt.min.time().replace(hour=hour)))
            target_times.append(target_dt)
        
        # 現在時刻から各時刻までの時間を計算
        hours_to_targets = []
        for target_time in target_times:
            hours_diff = (target_time - now_jst).total_seconds() / 3600
            hours_to_targets.append(hours_diff)
        
        # 最大の時間数を取得（4つの時刻すべてをカバーするため）
        max_hours = max(hours_to_targets)
        
        # 余裕を持たせて+1時間
        forecast_hours = max(int(max_hours) + 1, 1)
        
        # ログ出力で各時刻を表示
        time_info = []
        for i, (hour, hours_after) in enumerate(zip(target_hours, hours_to_targets)):
            time_info.append(f"{hour}時({hours_after:.1f}h後)")
        
        logger.info(f"翌日の4時刻: {', '.join(time_info)}, API取得時間: {forecast_hours}時間")
        
        # 4つの時刻すべてをカバーする時間でデータを取得
        return await self.get_forecast(lat, lon, forecast_hours=forecast_hours)

    async def test_specific_time_parameters(self, lat: float, lon: float) -> Dict[str, Any]:
        """特定時刻指定パラメータのテスト
        
        様々なパラメータでWxTech APIをテストし、特定時刻指定が可能か検証する
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            テスト結果とレスポンスデータ
        """
        import pytz
        from datetime import timedelta, datetime as dt
        import logging
        
        logger = logging.getLogger(__name__)
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = dt.now(jst)
        
        # 翌日の9時のタイムスタンプを作成
        target_date = now_jst.date() + timedelta(days=1)
        target_dt = jst.localize(dt.combine(target_date, dt.min.time().replace(hour=9)))
        target_timestamp = int(target_dt.timestamp())
        
        test_results = {}
        
        # テストパラメータのリスト
        test_params = [
            # 1. タイムスタンプ指定
            {
                "name": "timestamp",
                "params": {"lat": lat, "lon": lon, "timestamp": target_timestamp}
            },
            {
                "name": "timestamps", 
                "params": {"lat": lat, "lon": lon, "timestamps": str(target_timestamp)}
            },
            # 2. 開始・終了時刻指定
            {
                "name": "start_time",
                "params": {"lat": lat, "lon": lon, "start_time": target_timestamp}
            },
            {
                "name": "end_time",
                "params": {"lat": lat, "lon": lon, "start_time": target_timestamp, "end_time": target_timestamp + 3600}
            },
            # 3. 日時文字列指定
            {
                "name": "datetime",
                "params": {"lat": lat, "lon": lon, "datetime": target_dt.isoformat()}
            },
            {
                "name": "date_time",
                "params": {"lat": lat, "lon": lon, "date_time": target_dt.strftime("%Y-%m-%dT%H:%M:%S")}
            },
            # 4. 間隔指定
            {
                "name": "interval",
                "params": {"lat": lat, "lon": lon, "hours": 24, "interval": 3}
            },
            {
                "name": "step",
                "params": {"lat": lat, "lon": lon, "hours": 24, "step": 3}
            },
            # 5. 特定時刻リスト
            {
                "name": "times",
                "params": {"lat": lat, "lon": lon, "times": "9,12,15,18"}
            },
            {
                "name": "hours_list",
                "params": {"lat": lat, "lon": lon, "hours_list": "9,12,15,18"}
            }
        ]
        
        logger.info(f"🔍 WxTech API パラメータテスト開始 - ターゲット: {target_dt}")
        
        for test in test_params:
            try:
                logger.info(f"🧪 テスト: {test['name']} - {test['params']}")
                raw_data = await self._make_request("ss1wx", test['params'])
                
                # 成功した場合のレスポンス解析
                if "wxdata" in raw_data and raw_data["wxdata"]:
                    wxdata = raw_data["wxdata"][0]
                    srf_count = len(wxdata.get("srf", []))
                    mrf_count = len(wxdata.get("mrf", []))
                    
                    test_results[test['name']] = {
                        "success": True,
                        "srf_count": srf_count,
                        "mrf_count": mrf_count,
                        "response_size": len(str(raw_data)),
                        "first_srf_date": wxdata.get("srf", [{}])[0].get("date") if srf_count > 0 else None
                    }
                    logger.info(f"✅ {test['name']}: 成功 - srf={srf_count}, mrf={mrf_count}")
                else:
                    test_results[test['name']] = {
                        "success": False,
                        "error": "空のレスポンス"
                    }
                    logger.warning(f"⚠️ {test['name']}: 空のレスポンス")
                    
            except WxTechAPIError as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e),
                    "error_type": e.error_type,
                    "status_code": e.status_code
                }
                logger.error(f"❌ {test['name']}: APIエラー - {e.error_type}: {e}")
                
            except Exception as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e),
                    "error_type": "unknown"
                }
                logger.error(f"❌ {test['name']}: 不明エラー - {e}")
        
        # テスト結果のサマリー
        successful_tests = [name for name, result in test_results.items() if result.get("success", False)]
        logger.info(f"📊 テスト結果サマリー: {len(successful_tests)}/{len(test_params)} 成功")
        
        if successful_tests:
            logger.info(f"✅ 成功したパラメータ: {', '.join(successful_tests)}")
        
        return {
            "target_datetime": target_dt.isoformat(),
            "target_timestamp": target_timestamp,
            "test_results": test_results,
            "successful_params": successful_tests,
            "total_tests": len(test_params),
            "successful_count": len(successful_tests)
        }

    async def test_specific_times_only(self, lat: float, lon: float) -> Dict[str, Any]:
        """特定時刻のみのデータ取得テスト
        
        翌日の9,12,15,18時のみのデータが取得できるかテスト
        
        Args:
            lat: 緯度
            lon: 経度
            
        Returns:
            テスト結果とレスポンスデータの詳細解析
        """
        import pytz
        from datetime import timedelta, datetime as dt
        import logging
        
        logger = logging.getLogger(__name__)
        jst = pytz.timezone("Asia/Tokyo")
        now_jst = dt.now(jst)
        
        # 翌日の9, 12, 15, 18時JSTのタイムスタンプを作成
        target_date = now_jst.date() + timedelta(days=1)
        target_times = []
        target_timestamps = []
        
        for hour in [9, 12, 15, 18]:
            target_dt = jst.localize(dt.combine(target_date, dt.min.time().replace(hour=hour)))
            target_times.append(target_dt)
            target_timestamps.append(int(target_dt.timestamp()))
        
        timestamps_str = ",".join(map(str, target_timestamps))
        
        logger.info(f"🔍 特定時刻のみテスト開始")
        logger.info(f"📅 ターゲット時刻: {[t.strftime('%H:%M') for t in target_times]}")
        logger.info(f"🔢 タイムスタンプ: {timestamps_str}")
        
        test_results = {}
        
        # 最も有望なパラメータをテスト
        promising_params = [
            {
                "name": "timestamps_specific",
                "params": {"lat": lat, "lon": lon, "timestamps": timestamps_str}
            },
            {
                "name": "times_specific", 
                "params": {"lat": lat, "lon": lon, "times": "9,12,15,18"}
            },
            {
                "name": "hours_list_specific",
                "params": {"lat": lat, "lon": lon, "hours_list": "9,12,15,18"}
            },
            {
                "name": "start_end_time",
                "params": {
                    "lat": lat, 
                    "lon": lon, 
                    "start_time": target_timestamps[0],
                    "end_time": target_timestamps[-1]
                }
            },
            {
                "name": "reference_hours_1",
                "params": {"lat": lat, "lon": lon, "hours": 1}
            },
            {
                "name": "reference_hours_4",
                "params": {"lat": lat, "lon": lon, "hours": 4}
            }
        ]
        
        for test in promising_params:
            try:
                logger.info(f"🧪 テスト: {test['name']}")
                raw_data = await self._make_request("ss1wx", test['params'])
                
                if "wxdata" in raw_data and raw_data["wxdata"]:
                    wxdata = raw_data["wxdata"][0]
                    srf_data = wxdata.get("srf", [])
                    mrf_data = wxdata.get("mrf", [])
                    
                    # データの詳細解析
                    srf_times = [entry.get("date") for entry in srf_data[:10]]  # 最初の10件
                    mrf_times = [entry.get("date") for entry in mrf_data[:5]]   # 最初の5件
                    
                    test_results[test['name']] = {
                        "success": True,
                        "srf_count": len(srf_data),
                        "mrf_count": len(mrf_data),
                        "srf_sample_times": srf_times,
                        "mrf_sample_times": mrf_times,
                        "response_size": len(str(raw_data))
                    }
                    
                    logger.info(f"✅ {test['name']}: srf={len(srf_data)}, mrf={len(mrf_data)}")
                    logger.info(f"🕰️ 最初のsrf時刻: {srf_times[:3]}")
                    
                else:
                    test_results[test['name']] = {
                        "success": False,
                        "error": "空のレスポンス"
                    }
                    
            except Exception as e:
                test_results[test['name']] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ {test['name']}: {e}")
        
        return {
            "target_times": [t.isoformat() for t in target_times],
            "target_timestamps": target_timestamps,
            "test_results": test_results,
            "analysis": _analyze_response_patterns(test_results)
        }

    async def get_forecast_async(self, lat: float, lon: float, forecast_hours: int = 72) -> WeatherForecastCollection:
        """非同期で天気予報を取得

        Args:
            lat: 緯度
            lon: 経度
            forecast_hours: 予報時間数（デフォルト: 72時間）

        Returns:
            天気予報コレクション
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await self.get_forecast(lat, lon, forecast_hours)

    def _parse_forecast_response(
        self, raw_data: Dict[str, Any], location_name: str
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
                        forecast_data, location_name, is_hourly=True
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
                        forecast_data, location_name, is_hourly=False
                    )
                    forecasts.append(forecast)
                except Exception as e:
                    warnings.warn(f"日別予報の解析に失敗: {str(e)}")
                    continue

        return WeatherForecastCollection(location=location_name, forecasts=forecasts)

    def _parse_single_forecast(
        self, data: Dict[str, Any], location_name: str, is_hourly: bool = True
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
        forecast_datetime = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

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
            raw_data=data,
        )

    def _convert_weather_code(self, weather_code: str) -> WeatherCondition:
        """WxTech天気コードを標準的な天気状況に変換

        Args:
            weather_code: WxTech API の天気コード

        Returns:
            標準化された天気状況
        """
        # WxTech APIの天気コードマッピング（完全版）
        code_mapping = {
            # 晴れ系
            "100": WeatherCondition.CLEAR,
            "101": WeatherCondition.PARTLY_CLOUDY,  # 晴れ時々くもり
            "102": WeatherCondition.RAIN,           # 晴れ一時雨
            "103": WeatherCondition.RAIN,           # 晴れ時々雨
            "104": WeatherCondition.SNOW,           # 晴れ一時雪
            "105": WeatherCondition.SNOW,           # 晴れ時々雪
            "110": WeatherCondition.PARTLY_CLOUDY,
            "111": WeatherCondition.CLOUDY,         # 晴れのちくもり
            "112": WeatherCondition.RAIN,           # 晴れのち一時雨
            "113": WeatherCondition.RAIN,           # 晴れのち時々雨
            "114": WeatherCondition.RAIN,           # 晴れのち雨
            "115": WeatherCondition.SNOW,           # 晴れのち一時雪
            "116": WeatherCondition.SNOW,           # 晴れのち時々雪
            "117": WeatherCondition.SNOW,           # 晴れのち雪
            "119": WeatherCondition.THUNDER,        # 晴れのち雨か雷雨
            "123": WeatherCondition.THUNDER,        # 晴れ山沿い雷雨
            "125": WeatherCondition.THUNDER,        # 晴れ午後は雷雨
            "126": WeatherCondition.RAIN,           # 晴れ昼頃から雨
            "127": WeatherCondition.RAIN,           # 晴れ夕方から雨
            "128": WeatherCondition.RAIN,           # 晴れ夜は雨
            "129": WeatherCondition.RAIN,           # 晴れ夜半から雨
            "130": WeatherCondition.FOG,            # 朝の内霧のち晴れ
            "131": WeatherCondition.FOG,            # 晴れ朝方霧
            "132": WeatherCondition.PARTLY_CLOUDY,  # 晴れ時々くもり
            "140": WeatherCondition.RAIN,           # 晴れ時々雨
            
            # 曇り系
            "200": WeatherCondition.CLOUDY,
            "201": WeatherCondition.PARTLY_CLOUDY,  # くもり時々晴れ
            "202": WeatherCondition.RAIN,           # くもり一時雨
            "203": WeatherCondition.RAIN,           # くもり時々雨
            "204": WeatherCondition.SNOW,           # くもり一時雪
            "205": WeatherCondition.SNOW,           # くもり時々雪
            "208": WeatherCondition.THUNDER,        # くもり一時雨か雷雨
            "209": WeatherCondition.FOG,            # 霧
            "210": WeatherCondition.PARTLY_CLOUDY,  # くもりのち時々晴れ
            "211": WeatherCondition.CLEAR,          # くもりのち晴れ
            "212": WeatherCondition.RAIN,           # くもりのち一時雨
            "213": WeatherCondition.RAIN,           # くもりのち時々雨
            "214": WeatherCondition.RAIN,           # くもりのち雨
            "219": WeatherCondition.THUNDER,        # くもりのち雨か雷雨
            "224": WeatherCondition.RAIN,           # くもり昼頃から雨
            "225": WeatherCondition.RAIN,           # くもり夕方から雨
            "226": WeatherCondition.RAIN,           # くもり夜は雨
            "227": WeatherCondition.RAIN,           # くもり夜半から雨
            "231": WeatherCondition.FOG,            # くもり海上海岸は霧か霧雨
            "240": WeatherCondition.THUNDER,        # くもり時々雨で雷を伴う
            "250": WeatherCondition.THUNDER,        # くもり時々雪で雷を伴う
            
            # 雨系
            "300": WeatherCondition.RAIN,
            "301": WeatherCondition.RAIN,           # 雨時々晴れ
            "302": WeatherCondition.RAIN,           # 雨時々止む
            "303": WeatherCondition.RAIN,           # 雨時々雪
            "306": WeatherCondition.HEAVY_RAIN,     # 大雨
            "308": WeatherCondition.SEVERE_STORM,   # 雨で暴風を伴う
            "309": WeatherCondition.RAIN,           # 雨一時雪
            "311": WeatherCondition.RAIN,           # 雨のち晴れ
            "313": WeatherCondition.RAIN,           # 雨のちくもり
            "314": WeatherCondition.RAIN,           # 雨のち時々雪
            "315": WeatherCondition.RAIN,           # 雨のち雪
            "320": WeatherCondition.RAIN,           # 朝の内雨のち晴れ
            "321": WeatherCondition.RAIN,           # 朝の内雨のちくもり
            "323": WeatherCondition.RAIN,           # 雨昼頃から晴れ
            "324": WeatherCondition.RAIN,           # 雨夕方から晴れ
            "325": WeatherCondition.RAIN,           # 雨夜は晴れ
            "328": WeatherCondition.HEAVY_RAIN,     # 雨一時強く降る
            
            # 雪系
            "400": WeatherCondition.SNOW,
            "401": WeatherCondition.SNOW,           # 雪時々晴れ
            "402": WeatherCondition.SNOW,           # 雪時々止む
            "403": WeatherCondition.SNOW,           # 雪時々雨
            "405": WeatherCondition.HEAVY_SNOW,     # 大雪
            "406": WeatherCondition.SEVERE_STORM,   # 風雪強い
            "407": WeatherCondition.SEVERE_STORM,   # 暴風雪
            "409": WeatherCondition.SNOW,           # 雪一時雨
            "411": WeatherCondition.SNOW,           # 雪のち晴れ
            "413": WeatherCondition.SNOW,           # 雪のちくもり
            "414": WeatherCondition.SNOW,           # 雪のち雨
            "420": WeatherCondition.SNOW,           # 朝の内雪のち晴れ
            "421": WeatherCondition.SNOW,           # 朝の内雪のちくもり
            "422": WeatherCondition.SNOW,           # 雪昼頃から雨
            "423": WeatherCondition.SNOW,           # 雪夕方から雨
            "424": WeatherCondition.SNOW,           # 雪夜半から雨
            "425": WeatherCondition.HEAVY_SNOW,     # 雪一時強く降る
            "450": WeatherCondition.THUNDER,        # 雪で雷を伴う
            
            # 特殊系
            "350": WeatherCondition.THUNDER,        # 雷
            "500": WeatherCondition.CLEAR,          # 快晴
            "550": WeatherCondition.EXTREME_HEAT,   # 猫暮
            "552": WeatherCondition.EXTREME_HEAT,   # 猫暮時々曇り
            "553": WeatherCondition.EXTREME_HEAT,   # 猫暮時々雨
            "558": WeatherCondition.SEVERE_STORM,   # 猫暮時々大雨・嵐
            "562": WeatherCondition.EXTREME_HEAT,   # 猫暮のち曇り
            "563": WeatherCondition.EXTREME_HEAT,   # 猫暮のち雨
            "568": WeatherCondition.SEVERE_STORM,   # 猫暮のち大雨・嵐
            "572": WeatherCondition.EXTREME_HEAT,   # 曇り時々猫暮
            "573": WeatherCondition.EXTREME_HEAT,   # 雨時々猫暮
            "582": WeatherCondition.EXTREME_HEAT,   # 曇りのち猫暮
            "583": WeatherCondition.EXTREME_HEAT,   # 雨のち猫暮
            "600": WeatherCondition.CLOUDY,         # うすぐもり
            "650": WeatherCondition.RAIN,           # 小雨
            "800": WeatherCondition.THUNDER,        # 雷
            "850": WeatherCondition.SEVERE_STORM,   # 大雨・嵐
            "851": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々晴れ
            "852": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々曇り
            "853": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々雨
            "854": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々雪
            "855": WeatherCondition.SEVERE_STORM,   # 大雨・嵐時々猫暮
            "859": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち曇り
            "860": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雪
            "861": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雨
            "862": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち雪
            "863": WeatherCondition.SEVERE_STORM,   # 大雨・嵐のち猫暮
        }

        return code_mapping.get(weather_code, WeatherCondition.UNKNOWN)

    def _get_weather_description(self, weather_code: str) -> str:
        """天気コードから日本語説明を取得
        
        特殊気象条件（雷、霧）を含む完全版マッピング

        Args:
            weather_code: WxTech API の天気コード

        Returns:
            日本語の天気説明
        """
        # 完全な天気コードマッピング
        descriptions = {
            "100": "晴れ",
            "101": "晴れ時々くもり",
            "102": "晴れ一時雨",
            "103": "晴れ時々雨",
            "104": "晴れ一時雪",
            "105": "晴れ時々雪",
            "106": "晴れ一時雨か雪",
            "107": "晴れ時々雨か雪",
            "108": "晴れ一時雨",
            "110": "晴れのち時々くもり",
            "111": "晴れのちくもり",
            "112": "晴れのち一時雨",
            "113": "晴れのち時々雨",
            "114": "晴れのち雨",
            "115": "晴れのち一時雪",
            "116": "晴れのち時々雪",
            "117": "晴れのち雪",
            "118": "晴れのち雨か雪",
            "119": "晴れのち雨か雷雨",
            "120": "晴れ一時雨",
            "121": "晴れ一時雨",
            "122": "晴れ夕方一時雨",
            "123": "晴れ山沿い雷雨",
            "124": "晴れ山沿い雪",
            "125": "晴れ午後は雷雨",
            "126": "晴れ昼頃から雨",
            "127": "晴れ夕方から雨",
            "128": "晴れ夜は雨",
            "129": "晴れ夜半から雨",
            "130": "朝の内霧のち晴れ",
            "131": "晴れ朝方霧",
            "132": "晴れ時々くもり",
            "140": "晴れ時々雨",
            "160": "晴れ一時雪か雨",
            "170": "晴れ時々雪か雨",
            "181": "晴れのち雪か雨",
            "200": "くもり",
            "201": "くもり時々晴れ",
            "202": "くもり一時雨",
            "203": "くもり時々雨",
            "204": "くもり一時雪",
            "205": "くもり時々雪",
            "206": "くもり一時雨か雪",
            "207": "くもり時々雨か雪",
            "208": "くもり一時雨か雷雨",
            "209": "霧",
            "210": "くもりのち時々晴れ",
            "211": "くもりのち晴れ",
            "212": "くもりのち一時雨",
            "213": "くもりのち時々雨",
            "214": "くもりのち雨",
            "215": "くもりのち一時雪",
            "216": "くもりのち時々雪",
            "217": "くもりのち雪",
            "218": "くもりのち雨か雪",
            "219": "くもりのち雨か雷雨",
            "220": "くもり朝夕一時雨",
            "221": "くもり朝の内一時雨",
            "222": "くもり夕方一時雨",
            "223": "くもり日中時々晴れ",
            "224": "くもり昼頃から雨",
            "225": "くもり夕方から雨",
            "226": "くもり夜は雨",
            "227": "くもり夜半から雨",
            "228": "くもり昼頃から雪",
            "229": "くもり夕方から雪",
            "230": "くもり夜は雪",
            "231": "くもり海上海岸は霧か霧雨",
            "240": "くもり時々雨で雷を伴う",
            "250": "くもり時々雪で雷を伴う",
            "260": "くもり一時雪か雨",
            "270": "くもり時々雪か雨",
            "281": "くもりのち雪か雨",
            "300": "雨",
            "301": "雨時々晴れ",
            "302": "雨時々止む",
            "303": "雨時々雪",
            "304": "雨か雪",
            "306": "大雨",
            "308": "雨で暴風を伴う",
            "309": "雨一時雪",
            "311": "雨のち晴れ",
            "313": "雨のちくもり",
            "314": "雨のち時々雪",
            "315": "雨のち雪",
            "316": "雨か雪のち晴れ",
            "317": "雨か雪のちくもり",
            "320": "朝の内雨のち晴れ",
            "321": "朝の内雨のちくもり",
            "322": "雨朝晩一時雪",
            "323": "雨昼頃から晴れ",
            "324": "雨夕方から晴れ",
            "325": "雨夜は晴れ",
            "326": "雨夕方から雪",
            "327": "雨夜は雪",
            "328": "雨一時強く降る",
            "329": "雨一時みぞれ",
            "340": "雪か雨",
            "350": "雷",
            "361": "雪か雨のち晴れ",
            "371": "雪か雨のちくもり",
            "400": "雪",
            "401": "雪時々晴れ",
            "402": "雪時々止む",
            "403": "雪時々雨",
            "405": "大雪",
            "406": "風雪強い",
            "407": "暴風雪",
            "409": "雪一時雨",
            "411": "雪のち晴れ",
            "413": "雪のちくもり",
            "414": "雪のち雨",
            "420": "朝の内雪のち晴れ",
            "421": "朝の内雪のちくもり",
            "422": "雪昼頃から雨",
            "423": "雪夕方から雨",
            "424": "雪夜半から雨",
            "425": "雪一時強く降る",
            "426": "雪のちみぞれ",
            "427": "雪一時みぞれ",
            "430": "みぞれ",
            "450": "雪で雷を伴う",
            "500": "快晴",
            "550": "猛暑",
            "552": "猛暑時々曇り",
            "553": "猛暑時々雨",
            "558": "猛暑時々大雨・嵐",
            "562": "猛暑のち曇り",
            "563": "猛暑のち雨",
            "568": "猛暑のち大雨・嵐",
            "572": "曇り時々猛暑",
            "573": "雨時々猛暑",
            "582": "曇りのち猛暑",
            "583": "雨のち猛暑",
            "600": "うすぐもり",
            "650": "小雨",
            "800": "雷",
            "850": "大雨・嵐",
            "851": "大雨・嵐時々晴れ",
            "852": "大雨・嵐時々曇り",
            "853": "大雨・嵐時々雨",
            "854": "大雨・嵐時々雪",
            "855": "大雨・嵐時々猛暑",
            "859": "大雨・嵐のち曇り",
            "860": "大雨・嵐のち雪",
            "861": "大雨・嵐のち雨",
            "862": "大雨・嵐のち雪",
            "863": "大雨・嵐のち猛暑",
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
        if hasattr(self, "session"):
            self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def _analyze_response_patterns(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """レスポンスパターンを分析して特定時刻指定の効果を確認する"""
    
    analysis = {
        "unique_response_sizes": set(),
        "unique_srf_counts": set(),
        "unique_mrf_counts": set(),
        "minimum_data_response": None,
        "appears_time_specific": False
    }
    
    for name, result in test_results.items():
        if result.get("success"):
            analysis["unique_response_sizes"].add(result.get("response_size", 0))
            analysis["unique_srf_counts"].add(result.get("srf_count", 0))
            analysis["unique_mrf_counts"].add(result.get("mrf_count", 0))
            
            # 最小データレスポンスを特定
            if (analysis["minimum_data_response"] is None or 
                result.get("srf_count", 0) < analysis["minimum_data_response"]["srf_count"]):
                analysis["minimum_data_response"] = {
                    "name": name,
                    "srf_count": result.get("srf_count", 0),
                    "mrf_count": result.get("mrf_count", 0)
                }
    
    # 異なるデータサイズがあるかをチェック
    analysis["appears_time_specific"] = (
        len(analysis["unique_srf_counts"]) > 1 or 
        len(analysis["unique_response_sizes"]) > 1
    )
    
    # セットをリストに変換（JSONシリアライズ用）
    analysis["unique_response_sizes"] = sorted(list(analysis["unique_response_sizes"]))
    analysis["unique_srf_counts"] = sorted(list(analysis["unique_srf_counts"]))
    analysis["unique_mrf_counts"] = sorted(list(analysis["unique_mrf_counts"]))
    
    return analysis


# 既存の関数との互換性を保つためのラッパー関数
async def get_japan_1km_mesh_weather_forecast(
    lat: float, lon: float, api_key: str
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
        forecast_collection = await client.get_forecast_async(lat, lon, forecast_hours=72)
        return forecast_collection.to_dict()
    finally:
        client.close()
