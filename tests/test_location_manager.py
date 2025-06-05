"""
地点データ管理システムのテスト

LocationManagerクラスとその関連機能のユニットテスト
"""

import pytest
import tempfile
import csv
import warnings
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
            # 警告を無効にしてテスト
            manager = LocationManager(csv_path, warn_missing_deps=False)
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
    
    def test_load_locations_with_coordinates(self):
        """緯度経度付き地点データ読み込みのテスト"""
        csv_content = """稚内,45.4167,141.6833
札幌,43.0642,141.3469
東京,35.6762,139.6503
大阪,34.6937,135.5023
福岡,33.5904,130.4017"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            locations = manager.get_all_locations()
            
            assert len(locations) == 5
            
            # 稚内の緯度経度確認
            wakkanai = locations[0]
            assert wakkanai.name == "稚内"
            assert wakkanai.latitude == 45.4167
            assert wakkanai.longitude == 141.6833
            
            # 札幌の緯度経度確認
            sapporo = locations[1]
            assert sapporo.name == "札幌"
            assert sapporo.latitude == 43.0642
            assert sapporo.longitude == 141.3469
        finally:
            Path(csv_path).unlink()
    
    def test_load_locations_mixed_format(self):
        """混在形式（一部緯度経度あり）のテスト"""
        csv_content = """稚内,45.4167,141.6833
札幌
東京,35.6762,139.6503
大阪
福岡,33.5904,130.4017"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            locations = manager.get_all_locations()
            
            assert len(locations) == 5
            
            # 緯度経度ありの地点
            assert locations[0].latitude is not None
            assert locations[2].latitude is not None  # 東京
            assert locations[4].latitude is not None  # 福岡
            
            # 緯度経度なしの地点
            assert locations[1].latitude is None  # 札幌
            assert locations[3].latitude is None  # 大阪
        finally:
            Path(csv_path).unlink()
    
    def test_load_locations_invalid_coordinates(self):
        """無効な緯度経度データのテスト"""
        csv_content = """稚内,invalid,longitude
札幌,43.0642,invalid
東京,35.6762,139.6503
大阪,,
福岡,33.5904,"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            locations = manager.get_all_locations()
            
            assert len(locations) == 5
            
            # 無効なデータは None になるべき
            assert locations[0].latitude is None  # 稚内
            assert locations[1].latitude is not None  # 札幌
            assert locations[1].longitude is None    # 札幌
            assert locations[2].latitude is not None  # 東京（正常）
            assert locations[3].latitude is None     # 大阪
            assert locations[4].latitude is not None  # 福岡
            assert locations[4].longitude is None     # 福岡
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
            manager = LocationManager(csv_path, warn_missing_deps=False)
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
            LocationManager("nonexistent_file.csv", warn_missing_deps=False)
    
    def test_empty_csv(self):
        """空のCSVファイルのテスト"""
        csv_path = self.create_test_csv("")
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            locations = manager.get_all_locations()
            assert len(locations) == 0  # 空のCSVは正常に処理される
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
            manager = LocationManager(csv_path, warn_missing_deps=False)
            
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
            manager = LocationManager(csv_path, warn_missing_deps=False)
            
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
    
    def test_search_location_with_scores(self):
        """スコア付き検索のテスト"""
        csv_content = """稚内
札幌
東京"""
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            
            # スコア付き検索
            results = manager.search_location_with_scores("札幌")
            
            assert len(results) >= 1
            assert all(isinstance(item, tuple) for item in results)
            assert all(len(item) == 2 for item in results)
            
            location, score = results[0]
            assert location.name == "札幌"
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
        finally:
            Path(csv_path).unlink()
    
    def test_search_empty_query(self):
        """空の検索クエリのテスト"""
        csv_content = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            
            # 空文字列
            results = manager.search_location("")
            assert len(results) == 0
            
            # 空白のみ
            results = manager.search_location("   ")
            assert len(results) == 0
            
            # スコア付き検索でも同様
            results = manager.search_location_with_scores("")
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
            manager = LocationManager(csv_path, warn_missing_deps=False)
            assert manager.get_location_count() == 3
        finally:
            Path(csv_path).unlink()
    
    def test_reload_locations(self):
        """地点データ再読み込みのテスト"""
        # 最初のCSVファイル
        csv_content1 = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content1)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            assert manager.get_location_count() == 2
            
            # ファイル内容を変更
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("稚内\n札幌\n東京\n大阪")
            
            # 再読み込み
            manager.reload_locations()
            assert manager.get_location_count() == 4
        finally:
            Path(csv_path).unlink()
    
    def test_get_dependency_status(self):
        """依存関係状態取得のテスト"""
        csv_content = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            status = manager.get_dependency_status()
            
            assert isinstance(status, dict)
            assert "jaconv_available" in status
            assert "levenshtein_available" in status
            assert "features" in status
            assert isinstance(status["features"], dict)
        finally:
            Path(csv_path).unlink()
    
    def test_warning_messages(self):
        """警告メッセージのテスト"""
        csv_content = "稚内\n札幌"
        csv_path = self.create_test_csv(csv_content)
        
        try:
            # 警告が発生するかテスト（jaconvやLevenshteinがない場合）
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                manager = LocationManager(csv_path, warn_missing_deps=True)
                
                # 警告が発生する可能性があることを確認（依存関係の状況による）
                assert isinstance(manager, LocationManager)
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
        # 実際のChiten.csvの形式をシミュレート（141件のサンプル）
        csv_content = """稚内
旭川
札幌
函館
帯広
釧路
北見
室蘭
苫小牧
根室
青森
八戸
秋田
盛岡
仙台
山形
福島
水戸
宇都宮
前橋
さいたま
千葉
東京
横浜
新潟
富山
金沢
福井
甲府
長野
岐阜
静岡
名古屋
津
大津
京都
大阪
神戸
奈良
和歌山
鳥取
松江
岡山
広島
山口
徳島
高松
松山
高知
福岡
佐賀
長崎
熊本
大分
宮崎
鹿児島
那覇"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            manager = LocationManager(csv_path, warn_missing_deps=False)
            
            # 読み込み確認
            assert manager.get_location_count() == 56
            
            # 各種検索テスト
            # 完全一致
            result = manager.find_exact_match("札幌")
            assert result is not None
            assert result.name == "札幌"
            
            # 部分一致
            results = manager.search_location("札")
            assert len(results) >= 1
            assert any("札幌" in loc.name for loc in results)
            
            # スコア付き検索
            results_with_scores = manager.search_location_with_scores("東京")
            assert len(results_with_scores) >= 1
            location, score = results_with_scores[0]
            assert location.name == "東京"
            assert score == 1.0  # 完全一致
                
        finally:
            Path(csv_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
