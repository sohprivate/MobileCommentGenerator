"""ローカルCSVファイルからコメントデータを読み込むリポジトリ"""

import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from ..data.past_comment import PastComment, CommentType
from ..data.weather_data import WeatherForecast

logger = logging.getLogger(__name__)


class LocalCommentRepository:
    """ローカルCSVファイルからコメントを読み込む"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        # キャッシュを初期化時に読み込み
        self._comment_cache = None
        self._load_cache()
    
    def _read_csv_comments(self, file_path: Path, comment_type: str) -> List[PastComment]:
        """Read comments from a CSV file and convert to PastComment objects."""
        comments = []
        
        if not file_path.exists():
            logger.warning(f"CSV file not found: {file_path}")
            return comments
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Get the comment text (first column, which varies by type)
                    comment_text = row.get('weather_comment') or row.get('advice', '')
                    count = int(row.get('count', 0))
                    
                    if comment_text:
                        comment = PastComment(
                            location="全国",  # CSV doesn't have location info
                            datetime=datetime.now(),  # CSV doesn't have datetime info
                            weather_condition="不明",  # CSV doesn't have weather condition
                            comment_text=comment_text,
                            comment_type=CommentType.WEATHER_COMMENT if comment_type == "weather_comment" else CommentType.ADVICE,
                            raw_data={
                                'count': count,
                                'source': 'local_csv',
                                'file': file_path.name
                            }
                        )
                        comments.append(comment)
        
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
        
        return comments
    
    def _load_cache(self):
        """初期化時に全コメントをキャッシュに読み込み"""
        logger.info("Loading comment cache...")
        self._comment_cache = self._load_all_comments()
        logger.info(f"Loaded {len(self._comment_cache)} comments into cache")
    
    def _load_all_comments(self) -> List[PastComment]:
        """全季節の全コメントを読み込み"""
        all_comments = []
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        
        for season in seasons:
            # Read weather comments for this season
            weather_comment_file = self.output_dir / f"{season}_weather_comment_enhanced50.csv"
            weather_comments = self._read_csv_comments(weather_comment_file, "weather_comment")
            
            # Add season info to metadata
            for comment in weather_comments:
                comment.raw_data['season'] = season
            all_comments.extend(weather_comments)
            
            # Read advice comments for this season
            advice_file = self.output_dir / f"{season}_advice_enhanced50.csv"
            advice_comments = self._read_csv_comments(advice_file, "advice")
            
            # Add season info to metadata
            for comment in advice_comments:
                comment.raw_data['season'] = season
            all_comments.extend(advice_comments)
        
        return all_comments
    
    def get_all_available_comments(self, max_per_season_per_type: int = 20) -> List[PastComment]:
        """Get all available comments from all seasons for LLM to choose from."""
        if self._comment_cache is None:
            logger.warning("Comment cache not initialized, loading now...")
            self._load_cache()
        
        # キャッシュから季節別・タイプ別に制限して返す
        filtered_comments = []
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        
        for season in seasons:
            weather_comments = [c for c in (self._comment_cache or [])
                              if c.raw_data.get('season') == season and c.comment_type.value == 'weather_comment']
            advice_comments = [c for c in (self._comment_cache or [])
                             if c.raw_data.get('season') == season and c.comment_type.value == 'advice']
            
            filtered_comments.extend(weather_comments[:max_per_season_per_type])
            filtered_comments.extend(advice_comments[:max_per_season_per_type])
        
        logger.info(f"Retrieved {len(filtered_comments)} comments from cache for LLM selection")
        return filtered_comments
    
    def get_recent_comments(self, limit: int = 100) -> List[PastComment]:
        """全季節からコメントを取得してLLMに選択させる"""
        comments = self.get_all_available_comments(max_per_season_per_type=15)
        # 人気順でソート
        comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
        return comments[:limit]