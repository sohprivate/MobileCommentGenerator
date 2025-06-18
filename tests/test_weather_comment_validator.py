import pytest
from datetime import datetime
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection


def create_weather_forecast(description: str, temp: float = 20.0):
    return WeatherForecast(
        location="東京",
        datetime=datetime(2024, 6, 5, 9, 0, 0),
        temperature=temp,
        weather_code="100",
        weather_condition=WeatherCondition.CLEAR,
        weather_description=description,
        precipitation=0.0,
        humidity=50.0,
        wind_speed=1.0,
        wind_direction=WindDirection.N,
        wind_direction_degrees=0,
        pressure=1013.0,
        visibility=10.0,
        uv_index=0,
        confidence=1.0,
        raw_data={},
    )


def test_thin_cloud_no_cloudy_comment():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("薄曇り")
    is_valid, reason = validator._check_weather_reality_contradiction("雲が優勢です", weather)
    assert not is_valid
    assert "雲優勢" in reason


def test_thin_cloud_allows_sunny_comment():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("薄曇り")
    is_valid, reason = validator._check_weather_reality_contradiction("今日は晴れです", weather)
    assert is_valid


def test_thin_cloud_blocks_rain_comment():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("薄曇り")
    is_valid, reason = validator._check_weather_reality_contradiction("雨が降りそうです", weather)
    assert not is_valid
    assert "雨表現" in reason
