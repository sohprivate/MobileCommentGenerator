#!/usr/bin/env python3
"""Test weather API for all locations in 地点名.csv"""

import os
import sys
import csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.apis.wxtech_client import WxTechAPIClient
from src.config.weather_config import get_config

def test_all_locations():
    """Test weather API for all locations"""
    # Get config
    config = get_config()
    api_key = config.weather.wxtech_api_key
    
    if not api_key:
        print("ERROR: WXTECH_API_KEY environment variable not set")
        return
    
    # Read CSV file
    csv_path = "frontend/public/地点名.csv"
    locations = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append({
                'name': row['地点名'],
                'lat': float(row['緯度']),
                'lon': float(row['経度'])
            })
    
    print(f"Testing {len(locations)} locations...")
    
    # Create client
    client = WxTechAPIClient(api_key)
    
    success_count = 0
    error_count = 0
    errors = []
    
    # Test each location
    for i, loc in enumerate(locations):
        try:
            print(f"\n[{i+1}/{len(locations)}] Testing {loc['name']} (lat={loc['lat']}, lon={loc['lon']})...", end='')
            
            forecast_collection = client.get_forecast(loc['lat'], loc['lon'])
            
            if forecast_collection and forecast_collection.forecasts:
                print(f" ✓ Success! Got {len(forecast_collection.forecasts)} forecasts")
                success_count += 1
            else:
                print(f" ✗ No forecasts returned")
                error_count += 1
                errors.append(f"{loc['name']}: No forecasts returned")
                
        except Exception as e:
            print(f" ✗ ERROR: {str(e)}")
            error_count += 1
            errors.append(f"{loc['name']}: {str(e)}")
    
    client.close()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"Total locations: {len(locations)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    
    if errors:
        print(f"\nERROR DETAILS:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

if __name__ == "__main__":
    test_all_locations()