"""
地点データ管理システムのテスト

LocationManagerクラスとその関連機能のユニットテスト
"""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, mock_open

from src.data.location_manager import (
    Location,
    LocationManager,
    load_locations_from_csv,
    search_location
)


class TestLocation:
    """Locationデータクラスのテスト"""
    
    def test_location_creation(self):
        """Location作成のテスト"""
        location = Location(
            name="稚内",
            normalized_name="ワッカナイ",
            latitude=45.4167,
            longitude=141.6833
        )
        
        assert location.name == "稚内"
        assert location.normalized_name == "ワッカナイ"
        assert location.latitude == 45.4167
        assert location.longitude == 141.6833
    
    def test_location_optional_fields(self):
        """Location作成（緯度経度なし）のテスト"""
        location = Location(name="東京", normalized_name="トウキョウ")
        
        assert location.name == "東京"
        assert location.normalized_name == "トウキョウ"
        assert location.latitude is None
        assert location.longitude is None
    
    def test_location_string_representation(self):
        """Location文字列表現のテスト"""
        location = Location(name="大阪", normalized_name="オオサカ")
        str_repr = str(location)
        
        assert "大阪" in str_repr
        assert "オオサカ" in str_repr


class TestLocationManager:
    """LocationManagerクラスのテスト"""
    
    def create_test_csv(self, content: str) -> str:
        """テスト用CSVファイルを作成
        
        Args:
            content: CSVファイルの内容
            
        Returns:
            作成されたCSVファイルのパス
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def test_load_locations_success(self):
        """地点データ正常読み込みのテスト"""
        csv_content = """稚内
札幌
東京
大阪
福岡"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            locations = manager.get_all_locations()
            
            assert len(locations) == 5
            assert locations[0].name == "稚内"
            assert locations[1].name == "札幌"
            assert locations[2].name == "東京"
            assert locations[3].name == "大阪"
            assert locations[4].name == "福岡"
            
            # 正規化名が設定されていることを確認
            for location in locations:
                assert location.normalized_name
                assert location.normalized_name != ""
        finally:
            Path(csv_path).unlink()
    
    def test_load_locations_with_spaces(self):
        """空白を含む地点データ読み込みのテスト"""
        csv_content = """稚内
  札幌  
　東京　
大阪

福岡"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            locations = manager.get_all_locations()
            
            # 空行は除外されるべき
            assert len(locations) == 5
            
            # 空白は除去されるべき
            location_names = [loc.name for loc in locations]
            assert "札幌" in location_names
            assert "東京" in location_names
        finally:
            Path(csv_path).unlink()
    
    def test_file_not_found(self):
        """ファイルが存在しない場合のテスト"""
        with pytest.raises(FileNotFoundError):
            LocationManager("nonexistent_file.csv")
    
    def test_empty_csv(self):
        """空のCSVファイルのテスト"""
        csv_path = self.create_test_csv("")
        
        try:
            with pytest.raises(ValueError, match="CSVファイルが空です"):
                LocationManager(csv_path)
        finally:
            Path(csv_path).unlink()
    
    def test_search_exact_match(self):
        """完全一致検索のテスト"""
        csv_content = """稚内
札幌
東京都
大阪府
福岡"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            
            # 完全一致
            result = manager.find_exact_match("札幌")
            assert result is not None
            assert result.name == "札幌"
            
            # 存在しない地点
            result = manager.find_exact_match("京都")
            assert result is None
        finally:
            Path(csv_path).unlink()
    
    def test_search_partial_match(self):
        """部分一致検索のテスト"""
        csv_content = """稚内
札幌市
東京都
大阪府
福岡市"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            
            # 部分一致検索
            results = manager.search_location("札幌")
            assert len(results) >= 1
            assert any("札幌" in loc.name for loc in results)
            
            # 複数該当する検索
            results = manager.search_location("市")
            matching_results = [loc for loc in results if "市" in loc.name]
            assert len(matching_results) >= 2  # 札幌市、福岡市
        finally:
            Path(csv_path).unlink()
    
    def test_search_empty_query(self):
        """空の検索クエリのテスト"""
        csv_content = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            
            # 空文字列
            results = manager.search_location("")
            assert len(results) == 0
            
            # 空白のみ
            results = manager.search_location("   ")
            assert len(results) == 0
            
            # None (文字列変換される)
            results = manager.search_location("")
            assert len(results) == 0
        finally:
            Path(csv_path).unlink()
    
    def test_text_normalization(self):
        """テキスト正規化のテスト"""
        manager = LocationManager.__new__(LocationManager)  # __init__を呼ばずにインスタンス作成
        
        # 全角英数字の半角化
        assert manager._normalize_text("ＡＢＣＤ１２３４") == "ABCD1234"
        
        # 空白の除去
        assert manager._normalize_text("東 京 都") == "東京都"
        assert manager._normalize_text("　大　阪　") == "大阪"
        
        # 空文字列
        assert manager._normalize_text("") == ""
        assert manager._normalize_text(None) == ""
    
    def test_get_location_count(self):
        """地点数取得のテスト"""
        csv_content = """稚内
札幌
東京"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path)
            assert manager.get_location_count() == 3
        finally:
            Path(csv_path).unlink()
    
    def test_reload_locations(self):
        """地点データ再読み込みのテスト"""
        # 最初のCSVファイル
        csv_content1 = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content1)
        
        try:
            manager = LocationManager(csv_path)
            assert manager.get_location_count() == 2
            
            # ファイル内容を変更
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("稚内\n札幌\n東京\n大阪")
            
            # 再読み込み
            manager.reload_locations()
            assert manager.get_location_count() == 4
        finally:
            Path(csv_path).unlink()


class TestFunctionInterfaces:
    """関数インターフェースのテスト"""
    
    def create_test_csv(self, content: str) -> str:
        """テスト用CSVファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def test_load_locations_from_csv(self):
        """load_locations_from_csv関数のテスト"""
        csv_content = "稚内\n札幌\n東京"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            locations = load_locations_from_csv(csv_path)
            assert len(locations) == 3
            assert locations[0].name == "稚内"
        finally:
            Path(csv_path).unlink()
    
    def test_search_location_function(self):
        """search_location関数のテスト"""
        csv_content = "稚内\n札幌\n東京"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            results = search_location("札幌", csv_path)
            assert len(results) >= 1
            assert any("札幌" in loc.name for loc in results)
        finally:
            Path(csv_path).unlink()


class TestIntegration:
    """統合テスト"""
    
    def test_chiten_csv_format(self):
        """Chiten.csvフォーマット対応のテスト"""
        # 実際のChiten.csvの形式をシミュレート
        csv_content = """稚内
旭川
札幌
函館
帯広
釧路
北見
室蘭
苫小牧
根室"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            manager = LocationManager(csv_path)
            
            # 読み込み確認
            assert manager.get_location_count() == 10
            
            # 各種検索テスト
            # 完全一致
            result = manager.find_exact_match("札幌")
            assert result is not None
            assert result.name == "札幌"
            
            # 部分一致
            results = manager.search_location("札")
            assert len(results) >= 1
            assert any("札幌" in loc.name for loc in results)
            
            # あいまい検索
            results = manager.search_location("さっぽろ")  # ひらがな
            if results:  # jaconvが利用可能な場合のみ
                assert any("札幌" in loc.name for loc in results)
                
        finally:
            Path(csv_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
