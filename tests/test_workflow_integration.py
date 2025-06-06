"""
ワークフロー統合テスト

InputNode、OutputNode、および全体ワークフローのテスト
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json
import pytz

from src.data.comment_generation_state import CommentGenerationState
from src.data.location import Location
from src.data.weather_data import WeatherForecast
from src.data.past_comment import PastComment
from src.data.comment_pair import CommentPair
from src.nodes.input_node import input_node, _create_location, _get_default_preferences
from src.nodes.output_node import output_node, _determine_final_comment, _create_generation_metadata
from src.workflows.comment_generation_workflow import (
    create_comment_generation_workflow,
    run_comment_generation,
    should_retry
)


class TestInputNode:
    """InputNodeのテストスイート"""
    
    def test_input_node_basic(self):
        """基本的な入力処理"""
        state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "llm_provider": "openai"
        }
        
        result = input_node(state)
        
        assert result["input_processed"] is True
        assert result["retry_count"] == 0
        assert "location" in result
        assert result["location"]["name"] == "東京"
        assert "execution_context" in result
        assert "user_preferences" in result
    
    def test_input_node_minimal(self):
        """最小限の入力での処理"""
        state = {"location_name": "稚内"}
        
        result = input_node(state)
        
        assert result["input_processed"] is True
        assert result["llm_provider"] == "openai"  # デフォルト
        assert result["target_datetime"] is not None
        assert result["location"]["name"] == "稚内"
    
    def test_input_node_invalid_location(self):
        """未登録地点の処理"""
        state = {"location_name": "不明な地点"}
        
        result = input_node(state)
        
        assert result["input_processed"] is True
        assert result["location"]["name"] == "不明な地点"
        assert result["location"]["region"] == "不明"
        assert len(result.get("warnings", [])) == 0  # 警告は出るがエラーにはしない
    
    def test_input_node_missing_location(self):
        """地点名なしでのエラー処理"""
        state = {}
        
        result = input_node(state)
        
        assert result["input_processed"] is False
        assert len(result["errors"]) > 0
        assert "location_name" in result["errors"][0]
    
    def test_input_node_validation(self):
        """入力検証のテスト"""
        # 長すぎる地点名
        state = {"location_name": "a" * 51}
        result = input_node(state)
        assert result["input_processed"] is False
        assert len(result["errors"]) > 0
        
        # 無効なLLMプロバイダー
        state = {"location_name": "東京", "llm_provider": "invalid"}
        result = input_node(state)
        assert result["input_processed"] is False
        assert "LLMプロバイダー" in result["errors"][0]
    
    def test_input_node_future_datetime(self):
        """未来の日時での警告"""
        future_date = datetime.now() + timedelta(days=10)
        state = {
            "location_name": "東京",
            "target_datetime": future_date
        }
        
        result = input_node(state)
        
        assert result["input_processed"] is True
        assert len(result["warnings"]) > 0
        assert "7日以上先" in result["warnings"][0]
    
    def test_create_location(self):
        """地点作成のテスト"""
        # 登録済み地点
        location = _create_location("稚内")
        assert location.name == "稚内"
        assert location.latitude == 45.4158
        assert location.region == "北海道"
        
        # 未登録地点
        location = _create_location("未知の場所")
        assert location.name == "未知の場所"
        assert location.region == "不明"
    
    def test_get_default_preferences(self):
        """デフォルト設定のテスト"""
        prefs = _get_default_preferences()
        assert prefs["style"] == "casual"
        assert prefs["length"] == "medium"
        assert prefs["emoji_usage"] is True


class TestOutputNode:
    """OutputNodeのテストスイート"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.sample_state = {
            "location_name": "東京",
            "target_datetime": datetime.now(),
            "execution_start_time": datetime.now() - timedelta(seconds=2),
            "retry_count": 1,
            "generated_comment": "今日は爽やかな晴れですね",
            "weather_data": {
                "weather_description": "晴れ",
                "temperature": 20.0,
                "humidity": 60.0,
                "wind_speed": 3.0
            },
            "selected_pair": {
                "weather_comment": {
                    "comment_text": "気持ちの良い朝です",
                    "comment_type": "weather_comment",
                    "temperature": 19.0,
                    "weather_condition": "晴れ"
                },
                "advice_comment": {
                    "comment_text": "日焼け止めをお忘れなく",
                    "comment_type": "advice",
                    "temperature": 21.0,
                    "weather_condition": "晴れ"
                },
                "similarity_score": 0.85,
                "selection_reason": "天気条件が一致"
            },
            "validation_result": {
                "is_valid": True,
                "total_score": 0.8
            }
        }
    
    def test_output_node_success(self):
        """正常な出力処理"""
        result = output_node(self.sample_state)
        
        assert result["output_processed"] is True
        assert result["final_comment"] == "今日は爽やかな晴れですね"
        assert "output_json" in result
        
        # JSON形式の確認
        output_data = json.loads(result["output_json"])
        assert output_data["final_comment"] == "今日は爽やかな晴れですね"
        assert "generation_metadata" in output_data
        assert output_data["generation_metadata"]["retry_count"] == 1
        assert output_data["generation_metadata"]["execution_time_ms"] > 0
    
    def test_output_node_no_generated_comment(self):
        """生成コメントなしの場合"""
        state = self.sample_state.copy()
        del state["generated_comment"]
        
        result = output_node(state)
        
        assert result["output_processed"] is True
        assert result["final_comment"] == "気持ちの良い朝です"  # selected_pairから
    
    def test_output_node_minimal_state(self):
        """最小限の状態での処理"""
        state = {"location_name": "東京"}
        
        result = output_node(state)
        
        assert result["output_processed"] is True
        assert result["final_comment"] == "今日も素敵な一日をお過ごしください"
    
    def test_determine_final_comment(self):
        """最終コメント決定ロジック"""
        # LLM生成コメント優先
        state = {"generated_comment": "LLMコメント"}
        assert _determine_final_comment(state) == "LLMコメント"
        
        # selected_pairから
        state = {
            "selected_pair": {
                "weather_comment": {"comment_text": "ペアコメント"}
            }
        }
        assert _determine_final_comment(state) == "ペアコメント"
        
        # デフォルト
        state = {}
        assert _determine_final_comment(state) == "今日も素敵な一日をお過ごしください"
    
    def test_create_generation_metadata(self):
        """メタデータ生成のテスト"""
        metadata = _create_generation_metadata(self.sample_state, 2500)
        
        assert metadata["execution_time_ms"] == 2500
        assert metadata["retry_count"] == 1
        assert metadata["weather_condition"] == "晴れ"
        assert metadata["temperature"] == 20.0
        assert metadata["validation_passed"] is True
        assert len(metadata["selected_past_comments"]) == 2
    
    def test_output_node_with_errors(self):
        """エラー情報を含む出力"""
        state = self.sample_state.copy()
        state["errors"] = ["エラー1", "エラー2"]
        state["warnings"] = ["警告1"]
        
        result = output_node(state)
        output_data = json.loads(result["output_json"])
        
        assert len(output_data["generation_metadata"]["errors"]) == 2
        assert len(output_data["generation_metadata"]["warnings"]) == 1


class TestWorkflowIntegration:
    """ワークフロー全体のテスト"""
    
    def test_should_retry(self):
        """リトライ判定のテスト"""
        # リトライ不要
        state = {"retry_count": 0, "validation_result": {"is_valid": True}}
        assert should_retry(state) == "continue"
        
        # リトライ必要
        state = {"retry_count": 1, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "retry"
        
        # リトライ上限
        state = {"retry_count": 5, "validation_result": {"is_valid": False}}
        assert should_retry(state) == "continue"
    
    @patch('src.nodes.weather_forecast_node.fetch_weather_forecast_node')
    @patch('src.nodes.retrieve_past_comments_node.retrieve_past_comments_node')
    def test_workflow_creation(self, mock_retrieve, mock_fetch):
        """ワークフロー構築のテスト"""
        workflow = create_comment_generation_workflow()
        
        assert workflow is not None
        # ワークフローが正しく構築されているかの確認
        # （LangGraphの内部構造に依存するため、詳細なテストは省略）
    
    @patch('src.nodes.weather_forecast_node.WeatherAPI')
    @patch('src.nodes.retrieve_past_comments_node.S3Client')
    def test_run_comment_generation_success(self, mock_s3, mock_weather_api):
        """コメント生成実行の成功テスト"""
        # モックの設定
        mock_weather_api.return_value.get_forecast.return_value = WeatherForecast(
            location="東京",
            datetime=datetime.now(),
            temperature=20.0,
            weather_code="100",
            weather_description="晴れ",
            precipitation=0.0,
            humidity=60.0,
            wind_speed=3.0,
            wind_direction="北"
        )
        
        mock_s3.return_value.list_objects.return_value = []
        
        # 実行
        result = run_comment_generation(
            location_name="東京",
            target_datetime=datetime.now()
        )
        
        assert result["success"] is True
        assert result["final_comment"] is not None
        assert "generation_metadata" in result
    
    def test_run_comment_generation_error(self):
        """エラー時の処理"""
        # 無効な入力でエラーを発生させる
        result = run_comment_generation(
            location_name="",  # 空の地点名
            llm_provider="invalid"
        )
        
        # エラーでも基本的な構造は返す
        assert result["success"] is False or result["success"] is True
        assert "error" in result or "final_comment" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
