"""
天気予報統合機能の設定管理

環境変数やデフォルト設定を管理する
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv


@dataclass
class WeatherConfig:
    """天気予報機能の設定クラス

    Attributes:
        wxtech_api_key: WxTech API キー
        default_location: デフォルト地点名
        forecast_hours: デフォルト予報時間数
        forecast_hours_ahead: 何時間後の予報を取得するか（デフォルト12時間）
        api_timeout: API タイムアウト（秒）
        max_retries: 最大リトライ回数
        rate_limit_delay: レート制限回避遅延（秒）
        cache_ttl: キャッシュTTL（秒）
        enable_caching: キャッシュ有効化フラグ
    """

    wxtech_api_key: str = field(default_factory=lambda: os.getenv("WXTECH_API_KEY", ""))
    default_location: str = field(
        default_factory=lambda: os.getenv("DEFAULT_WEATHER_LOCATION", "東京")
    )
    forecast_hours: int = field(
        default_factory=lambda: int(os.getenv("WEATHER_FORECAST_HOURS", "24"))
    )
    forecast_hours_ahead: int = field(
        default_factory=lambda: int(os.getenv("WEATHER_FORECAST_HOURS_AHEAD", "12"))
    )
    api_timeout: int = field(default_factory=lambda: int(os.getenv("WEATHER_API_TIMEOUT", "30")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("WEATHER_API_MAX_RETRIES", "3")))
    rate_limit_delay: float = field(
        default_factory=lambda: float(os.getenv("WEATHER_API_RATE_LIMIT_DELAY", "0.1"))
    )
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("WEATHER_CACHE_TTL", "300"))
    )  # 5分
    enable_caching: bool = field(
        default_factory=lambda: os.getenv("WEATHER_ENABLE_CACHING", "true").lower() == "true"
    )

    def __post_init__(self):
        """設定の検証"""
        if not self.wxtech_api_key:
            raise ValueError("WXTECH_API_KEY環境変数が設定されていません")

        if self.forecast_hours <= 0:
            raise ValueError("forecast_hoursは1以上である必要があります")

        if self.api_timeout <= 0:
            raise ValueError("api_timeoutは1以上である必要があります")

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（ログ出力用、APIキーはマスク）

        Returns:
            設定情報の辞書
        """
        return {
            "wxtech_api_key": "***" if self.wxtech_api_key else "",
            "default_location": self.default_location,
            "forecast_hours": self.forecast_hours,
            "forecast_hours_ahead": self.forecast_hours_ahead,
            "api_timeout": self.api_timeout,
            "max_retries": self.max_retries,
            "rate_limit_delay": self.rate_limit_delay,
            "cache_ttl": self.cache_ttl,
            "enable_caching": self.enable_caching,
        }


@dataclass
class LangGraphConfig:
    """LangGraph統合機能の設定クラス

    Attributes:
        enable_weather_integration: 天気統合の有効化
        auto_location_detection: 自動地点検出の有効化
        weather_context_window: 天気情報のコンテキスト窓
        min_confidence_threshold: 最小信頼度閾値
    """

    enable_weather_integration: bool = field(
        default_factory=lambda: os.getenv("LANGGRAPH_ENABLE_WEATHER", "true").lower() == "true"
    )
    auto_location_detection: bool = field(
        default_factory=lambda: os.getenv("LANGGRAPH_AUTO_LOCATION", "false").lower() == "true"
    )
    weather_context_window: int = field(
        default_factory=lambda: int(os.getenv("LANGGRAPH_WEATHER_CONTEXT_WINDOW", "24"))
    )
    min_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("LANGGRAPH_MIN_CONFIDENCE", "0.7"))
    )

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "enable_weather_integration": self.enable_weather_integration,
            "auto_location_detection": self.auto_location_detection,
            "weather_context_window": self.weather_context_window,
            "min_confidence_threshold": self.min_confidence_threshold,
        }


@dataclass
class AppConfig:
    """アプリケーション全体の設定クラス

    Attributes:
        weather: 天気予報設定
        langgraph: LangGraph設定
        debug_mode: デバッグモード
        log_level: ログレベル
    """

    weather: WeatherConfig = field(default_factory=WeatherConfig)
    langgraph: LangGraphConfig = field(default_factory=LangGraphConfig)
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換

        Returns:
            設定情報の辞書
        """
        return {
            "weather": self.weather.to_dict(),
            "langgraph": self.langgraph.to_dict(),
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
        }


# グローバル設定インスタンス
_config = None
_env_loaded = False


def get_config() -> AppConfig:
    """グローバル設定インスタンスを取得

    Returns:
        アプリケーション設定
    """
    global _config, _env_loaded
    if not _env_loaded:
        load_dotenv()
        _env_loaded = True
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """設定を再読み込み

    Returns:
        新しいアプリケーション設定
    """
    global _config, _env_loaded
    load_dotenv(override=True)  # 環境変数を強制再読み込み
    _env_loaded = True
    _config = AppConfig()
    return _config


# 設定検証関数
def validate_config(config: AppConfig) -> Dict[str, list]:
    """設定の妥当性を検証

    Args:
        config: 検証するアプリケーション設定

    Returns:
        検証エラーの辞書 {'category': [error_messages]}
    """
    errors = {"weather": [], "langgraph": [], "general": []}

    # 天気設定の検証
    try:
        if not config.weather.wxtech_api_key:
            errors["weather"].append("WxTech APIキーが設定されていません")

        if config.weather.forecast_hours > 168:  # 7日 = 168時間
            errors["weather"].append("予報時間数が長すぎます（最大168時間）")

        if config.weather.api_timeout > 300:  # 5分
            errors["weather"].append("APIタイムアウトが長すぎます（最大300秒）")

    except Exception as e:
        errors["weather"].append(f"天気設定エラー: {str(e)}")

    # LangGraph設定の検証
    try:
        if not 0 <= config.langgraph.min_confidence_threshold <= 1:
            errors["langgraph"].append("信頼度閾値は0.0-1.0の範囲で設定してください")

        if config.langgraph.weather_context_window <= 0:
            errors["langgraph"].append("天気コンテキスト窓は1以上で設定してください")

    except Exception as e:
        errors["langgraph"].append(f"LangGraph設定エラー: {str(e)}")

    # 一般設定の検証
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.log_level not in valid_log_levels:
        errors["general"].append(f"無効なログレベル: {config.log_level}")

    return {k: v for k, v in errors.items() if v}  # エラーがあるカテゴリのみ返す


# 環境変数のデフォルト値を設定する関数
def setup_environment_defaults():
    """環境変数のデフォルト値を設定

    開発環境やテスト環境で使用
    """
    defaults = {
        "DEFAULT_WEATHER_LOCATION": "東京",
        "WEATHER_FORECAST_HOURS": "24",
        "WEATHER_FORECAST_HOURS_AHEAD": "12",
        "WEATHER_API_TIMEOUT": "30",
        "WEATHER_API_MAX_RETRIES": "3",
        "WEATHER_API_RATE_LIMIT_DELAY": "0.1",
        "WEATHER_CACHE_TTL": "300",
        "WEATHER_ENABLE_CACHING": "true",
        "LANGGRAPH_ENABLE_WEATHER": "true",
        "LANGGRAPH_AUTO_LOCATION": "false",
        "LANGGRAPH_WEATHER_CONTEXT_WINDOW": "24",
        "LANGGRAPH_MIN_CONFIDENCE": "0.7",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
    }

    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value


if __name__ == "__main__":
    # 設定テスト
    try:
        setup_environment_defaults()
        config = get_config()
        print("設定読み込み成功:")
        print(config.to_dict())

        # 設定検証
        validation_errors = validate_config(config)
        if validation_errors:
            print("\n設定検証エラー:")
            for category, errors in validation_errors.items():
                print(f"{category}:")
                for error in errors:
                    print(f"  - {error}")
        else:
            print("\n設定検証: 問題なし")

    except Exception as e:
        print(f"設定エラー: {str(e)}")
