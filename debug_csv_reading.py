#!/usr/bin/env python3
"""CSVファイル読み込みのデバッグスクリプト"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import csv
from pathlib import Path


def debug_csv_files():
    """enhanced100.csvファイルの読み込みをデバッグ"""
    
    output_dir = Path("output")
    seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
    
    for season in seasons:
        print(f"\n📂 季節「{season}」のファイルチェック:")
        
        # 天気コメントファイル
        weather_file = output_dir / f"{season}_weather_comment_enhanced100.csv"
        print(f"  天気コメントファイル: {weather_file}")
        print(f"  存在: {weather_file.exists()}")
        
        if weather_file.exists():
            try:
                with open(weather_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    print(f"  行数: {len(rows)}行")
                    if rows:
                        print(f"  カラム: {list(rows[0].keys())}")
                        print(f"  サンプル: {rows[0]}")
            except Exception as e:
                print(f"  ❌ 読み込みエラー: {e}")
        
        # アドバイスファイル
        advice_file = output_dir / f"{season}_advice_enhanced100.csv"
        print(f"  アドバイスファイル: {advice_file}")
        print(f"  存在: {advice_file.exists()}")
        
        if advice_file.exists():
            try:
                with open(advice_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    print(f"  行数: {len(rows)}行")
                    if rows:
                        print(f"  カラム: {list(rows[0].keys())}")
                        print(f"  サンプル: {rows[0]}")
            except Exception as e:
                print(f"  ❌ 読み込みエラー: {e}")


if __name__ == "__main__":
    debug_csv_files()