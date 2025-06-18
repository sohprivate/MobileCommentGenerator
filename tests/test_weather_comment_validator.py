import pytest
from datetime import datetime
from src.utils.weather_comment_validator import WeatherCommentValidator
from src.data.weather_data import WeatherForecast, WeatherCondition, WindDirection


def make_weather(description: str, temp: float = 20.0):
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
    weather = make_weather("薄曇り")
    is_valid, reason = validator._check_weather_reality_contradiction("雲が優勢です", weather)
    assert not is_valid
    assert "雲優勢" in reason
