"""設定ファイルの読み込みユーティリティ"""

import yaml
import os
from typing import Dict, Any

_config_cache = {}


def load_config(config_name: str) -> Dict[str, Any]:
    """YAMLファイルから設定を読み込む
    
    Args:
        config_name: 設定ファイル名（拡張子なし）
        
    Returns:
        設定の辞書
    """
    if config_name in _config_cache:
        return _config_cache[config_name]
    
    config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
    config_path = os.path.join(config_dir, f"{config_name}.yaml")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    _config_cache[config_name] = config
    return config


def get_weather_thresholds() -> Dict[str, Any]:
    """天気関連の閾値設定を取得"""
    return load_config('weather_thresholds')