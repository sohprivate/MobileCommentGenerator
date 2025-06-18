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


def test_temperature_symptom_contradiction_hot():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("晴れ", temp=30.0)
    is_valid, reason = validator._check_temperature_symptom_contradiction(
        "暑いです", "熱中症対策必須", weather
    )
    assert not is_valid
    assert "過度な熱中症対策" in reason


def test_temperature_symptom_contradiction_cold():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("晴れ", temp=20.0)
    is_valid, reason = validator._check_temperature_symptom_contradiction(
        "涼しいです", "厚着必須", weather
    )
    assert not is_valid
    assert "過度な防寒対策" in reason


def test_tone_contradiction_unstable_outing():
    validator = WeatherCommentValidator()
    weather = create_weather_forecast("曇り")
    is_valid, reason = validator._check_tone_contradiction(
        "空が不安定です", "お出かけ日和", weather
    )
    assert not is_valid
    assert "外出推奨" in reason


def test_umbrella_redundancy_both_necessity():
    validator = WeatherCommentValidator()
    is_valid, reason = validator._check_umbrella_redundancy(
        "傘を忘れずに", "傘の携帯を",
    )
    assert not is_valid
    assert "傘の必要性" in reason
