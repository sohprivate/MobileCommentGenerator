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
    
    def get_all_available_comments(self, max_per_season_per_type: int = 10) -> List[PastComment]:
        """Get all available comments from all seasons for LLM to choose from."""
        all_comments = []
        
        seasons = ["春", "夏", "秋", "冬", "梅雨", "台風"]
        
        for season in seasons:
            # Read weather comments for this season
            weather_comment_file = self.output_dir / f"{season}_weather_comment_top30.csv"
            weather_comments = self._read_csv_comments(weather_comment_file, "weather_comment")
            
            # Add season info to metadata
            for comment in weather_comments[:max_per_season_per_type]:
                comment.raw_data['season'] = season
            all_comments.extend(weather_comments[:max_per_season_per_type])
            
            # Read advice comments for this season
            advice_file = self.output_dir / f"{season}_advice_top30.csv"
            advice_comments = self._read_csv_comments(advice_file, "advice")
            
            # Add season info to metadata
            for comment in advice_comments[:max_per_season_per_type]:
                comment.raw_data['season'] = season
            all_comments.extend(advice_comments[:max_per_season_per_type])
        
        logger.info(f"Retrieved {len(all_comments)} comments from all seasons for LLM selection")
        return all_comments
    
    def get_recent_comments(self, weather_forecast: WeatherForecast, limit: int = 100) -> List[PastComment]:
        """全季節からコメントを取得してLLMに選択させる"""
        comments = self.get_all_available_comments(max_per_season_per_type=8)
        # 人気順でソート
        comments.sort(key=lambda x: x.raw_data.get('count', 0), reverse=True)
        return comments[:limit]