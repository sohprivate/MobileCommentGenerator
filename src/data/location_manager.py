"""
地点データ管理システム

このモジュールは、Chiten.csvファイルから地点情報を読み込み、
地点検索、データ正規化などの機能を提供します。
"""

from dataclasses import dataclass
from typing import List, Optional, Union, Tuple
import csv
import re
import unicodedata
import warnings
from pathlib import Path

try:
    import jaconv
    JACONV_AVAILABLE = True
except ImportError:
    JACONV_AVAILABLE = False

try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False


@dataclass
class Location:
    """地点情報を表すデータクラス
    
    Attributes:
        name: 元の地点名
        normalized_name: 正規化済み地点名
        latitude: 緯度（オプション）
        longitude: 経度（オプション）
    """
    name: str
    normalized_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def __str__(self) -> str:
        return f"Location(name='{self.name}', normalized='{self.normalized_name}')"

    def __repr__(self) -> str:
        return self.__str__()


class LocationManager:
    """地点データ管理クラス
    
    CSVファイルからの地点データ読み込み、検索、正規化機能を提供。
    """
    
    def __init__(self, csv_path: str = "Chiten.csv", warn_missing_deps: bool = True):
        """LocationManagerを初期化
        
        Args:
            csv_path: 地点データCSVファイルのパス
            warn_missing_deps: オプショナル依存関係の警告を表示するか
        """
        self.csv_path = csv_path
        self._locations: List[Location] = []
        
        # オプショナルライブラリの警告
        if warn_missing_deps:
            if not JACONV_AVAILABLE:
                warnings.warn(
                    "jaconv not available. ひらがな・カタカナ正規化が無効です。"
                    "pip install jaconv でインストールできます。",
                    UserWarning
                )
            if not LEVENSHTEIN_AVAILABLE:
                warnings.warn(
                    "python-Levenshtein not available. 高度な類似度検索が無効です。"
                    "pip install python-Levenshtein でインストールできます。",
                    UserWarning
                )
        
        self._load_locations()

    def _normalize_text(self, text: str) -> str:
        """テキストの正規化処理
        
        Args:
            text: 正規化対象のテキスト
            
        Returns:
            正規化されたテキスト
        """
        if not text:
            return ""
        
        # Unicode正規化（NFKC）
        normalized = unicodedata.normalize('NFKC', text)
        
        # 空白文字の除去
        normalized = re.sub(r'\s+', '', normalized)
        
        # 全角英数字を半角に変換
        normalized = normalized.translate(str.maketrans(
            '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
            '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        ))
        
        # ひらがな・カタカナの統一（カタカナに統一）
        if JACONV_AVAILABLE:
            normalized = jaconv.hira2kata(normalized)
        
        return normalized

    def _load_locations(self) -> None:
        """CSVファイルから地点データを読み込み"""
        csv_file = Path(self.csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"地点データファイルが見つかりません: {self.csv_path}")
        
        self._locations = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                for row_num, row in enumerate(reader, start=1):
                    # 空行やデータなしの行をスキップ
                    if not row or not row[0] or not row[0].strip():
                        continue
                    
                    location_name = row[0].strip()
                    normalized_name = self._normalize_text(location_name)
                    
                    # 緯度経度データが含まれる場合の処理
                    latitude = None
                    longitude = None
                    
                    if len(row) >= 3:
                        try:
                            latitude = float(row[1]) if row[1] and row[1].strip() else None
                            longitude = float(row[2]) if row[2] and row[2].strip() else None
                        except (ValueError, IndexError):
                            # 緯度経度の変換に失敗した場合はNoneのまま
                            pass
                    
                    location = Location(
                        name=location_name,
                        normalized_name=normalized_name,
                        latitude=latitude,
                        longitude=longitude
                    )
                    self._locations.append(location)
                        
        except Exception as e:
            raise RuntimeError(f"地点データの読み込みに失敗しました: {str(e)}")
    
    def get_all_locations(self) -> List[Location]:
        """すべての地点データを取得
        
        Returns:
            すべての地点のリスト
        """
        return self._locations.copy()
    
    def search_location(self, query: str) -> List[Location]:
        """地点名で検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            マッチした地点のリスト（類似度順）
        """
        if not query or not query.strip():
            return []
        
        normalized_query = self._normalize_text(query.strip())
        results = []
        
        for location in self._locations:
            score = self._calculate_similarity_score(normalized_query, location)
            if score > 0:
                results.append((location, score))
        
        # スコア順にソート（降順）
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [location for location, _ in results]
    
    def search_location_with_scores(self, query: str) -> List[Tuple[Location, float]]:
        """地点名で検索（スコア付き）
        
        Args:
            query: 検索クエリ
            
        Returns:
            (地点, スコア)のタプルのリスト（類似度順）
        """
        if not query or not query.strip():
            return []
        
        normalized_query = self._normalize_text(query.strip())
        results = []
        
        for location in self._locations:
            score = self._calculate_similarity_score(normalized_query, location)
            if score > 0:
                results.append((location, score))
        
        # スコア順にソート（降順）
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def find_exact_match(self, query: str) -> Optional[Location]:
        """完全一致で地点を検索
        
        Args:
            query: 検索クエリ
            
        Returns:
            完全一致した地点（なければNone）
        """
        normalized_query = self._normalize_text(query.strip())
        
        for location in self._locations:
            if (location.normalized_name == normalized_query or 
                self._normalize_text(location.name) == normalized_query):
                return location
        
        return None
    
    def _calculate_similarity_score(self, query: str, location: Location) -> float:
        """類似度スコアを計算
        
        Args:
            query: 検索クエリ（正規化済み）
            location: 地点オブジェクト
            
        Returns:
            類似度スコア（0.0-1.0）
        """
        target = location.normalized_name
        original_target = self._normalize_text(location.name)
        
        # 完全一致
        if query == target or query == original_target:
            return 1.0
        
        # 前方一致
        if target.startswith(query) or original_target.startswith(query):
            return 0.9
        
        # 部分一致
        if query in target or query in original_target:
            return 0.8
        
        # レーベンシュタイン距離による類似度
        if LEVENSHTEIN_AVAILABLE and len(query) >= 2:
            # より長い文字列との距離を計算
            longer_target = target if len(target) >= len(original_target) else original_target
            
            distance = Levenshtein.distance(query, longer_target)
            max_len = max(len(query), len(longer_target))
            
            if max_len > 0:
                similarity = 1.0 - (distance / max_len)
                # 閾値以上の場合のみ返す
                return similarity if similarity >= 0.6 else 0.0
        
        return 0.0
    
    def get_location_count(self) -> int:
        """読み込まれた地点数を取得
        
        Returns:
            地点数
        """
        return len(self._locations)
    
    def reload_locations(self) -> None:
        """地点データを再読み込み"""
        self._load_locations()
    
    def get_dependency_status(self) -> dict:
        """オプショナル依存関係の状態を取得
        
        Returns:
            依存関係の状態辞書
        """
        return {
            "jaconv_available": JACONV_AVAILABLE,
            "levenshtein_available": LEVENSHTEIN_AVAILABLE,
            "features": {
                "hiragana_katakana_normalization": JACONV_AVAILABLE,
                "advanced_similarity_search": LEVENSHTEIN_AVAILABLE
            }
        }


def load_locations_from_csv(csv_path: str = "Chiten.csv") -> List[Location]:
    """CSVファイルから地点データを読み込み
    
    Args:
        csv_path: CSVファイルのパス
        
    Returns:
        地点データのリスト
    """
    manager = LocationManager(csv_path, warn_missing_deps=False)
    return manager.get_all_locations()


def search_location(query: str, csv_path: str = "Chiten.csv") -> List[Location]:
    """地点名で検索（関数インターフェース）
    
    Args:
        query: 検索クエリ
        csv_path: CSVファイルのパス
        
    Returns:
        マッチした地点のリスト
    """
    manager = LocationManager(csv_path, warn_missing_deps=False)
    return manager.search_location(query)
