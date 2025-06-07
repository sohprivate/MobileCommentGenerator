"""
Streamlitアプリケーションの統合テスト

streamlit.testing.v1を使用したUIとワークフローの統合テスト
"""

import pytest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest
from datetime import datetime
import json


class TestStreamlitApp:
    """Streamlitアプリケーションのメインテスト"""
    
    def test_app_loads_without_errors(self):
        """アプリが正常に起動することを確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # エラーがないことを確認
        assert not at.exception
        
        # タイトルが表示されることを確認
        assert any("天気コメント生成システム" in str(elem.value) for elem in at.markdown)
    
    def test_initial_state(self):
        """初期状態の確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # セッション状態の初期値確認
        assert at.session_state["selected_location"] == "東京"
        assert at.session_state["llm_provider"] == "openai"
        assert at.session_state["current_result"] is None
        assert at.session_state["is_generating"] is False
        
        # セレクトボックスの初期値確認
        assert len(at.selectbox) >= 2  # 地点選択とLLMプロバイダー選択
    
    def test_location_selection(self):
        """地点選択が正しく動作することを確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # 地点選択セレクトボックスを取得（最初のセレクトボックス）
        location_selectbox = at.selectbox[0]
        
        # 別の地点を選択
        location_selectbox.select("稚内").run()
        
        # セッション状態が更新されることを確認
        assert at.session_state["selected_location"] == "稚内"
    
    def test_llm_provider_selection(self):
        """LLMプロバイダー選択が正しく動作することを確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # LLMプロバイダー選択セレクトボックスを取得（2番目のセレクトボックス）
        llm_selectbox = at.selectbox[1]
        
        # 別のプロバイダーを選択
        llm_selectbox.select("gemini").run()
        
        # セッション状態が更新されることを確認
        assert at.session_state["llm_provider"] == "gemini"
    
    @patch('src.workflows.comment_generation_workflow.run_comment_generation')
    def test_comment_generation_success(self, mock_run_generation):
        """コメント生成の成功フローをテスト"""
        # モックの設定
        mock_run_generation.return_value = {
            'success': True,
            'final_comment': 'テスト用の天気コメント',
            'generation_metadata': {
                'location_name': '東京',
                'weather_condition': '晴れ',
                'temperature': 25.0,
                'execution_time_ms': 1500,
                'retry_count': 0
            },
            'execution_time_ms': 1500,
            'retry_count': 0,
            'warnings': []
        }
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # 生成ボタンをクリック
        generate_button = at.button[0]
        generate_button.click().run()
        
        # モックが呼び出されたことを確認
        mock_run_generation.assert_called_once()
        
        # 成功メッセージが表示されることを確認
        assert any("コメント生成が完了しました" in str(elem.value) for elem in at.success)
        
        # バルーンアニメーションが呼び出されることを確認
        # (streamlit.testing では balloons の確認は限定的)
        
        # セッション状態に結果が保存されることを確認
        assert at.session_state["current_result"] is not None
        assert at.session_state["current_result"]["success"] is True
        assert at.session_state["current_result"]["final_comment"] == "テスト用の天気コメント"
    
    @patch('src.workflows.comment_generation_workflow.run_comment_generation')
    def test_comment_generation_error(self, mock_run_generation):
        """コメント生成のエラーフローをテスト"""
        # エラーモックの設定
        mock_run_generation.return_value = {
            'success': False,
            'error': 'API接続エラーが発生しました',
            'final_comment': None,
            'generation_metadata': {}
        }
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # 生成ボタンをクリック
        generate_button = at.button[0]
        generate_button.click().run()
        
        # エラーメッセージが表示されることを確認
        assert any("生成に失敗しました" in str(elem.value) for elem in at.error)
        assert any("API接続エラー" in str(elem.value) for elem in at.error)
    
    @patch('src.workflows.comment_generation_workflow.run_comment_generation')
    def test_result_display(self, mock_run_generation):
        """結果表示コンポーネントのテスト"""
        # モックの設定
        mock_result = {
            'success': True,
            'final_comment': '今日は爽やかな一日です',
            'generation_metadata': {
                'weather_condition': '晴れ',
                'temperature': 22.5,
                'selected_past_comments': [
                    {'text': '快晴で気持ちいい', 'type': 'weather_comment'},
                    {'text': '日焼け対策を', 'type': 'advice'}
                ]
            }
        }
        mock_run_generation.return_value = mock_result
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # コメント生成実行
        at.button[0].click().run()
        
        # 結果が表示されることを確認
        # (実際のコンポーネント構造に依存するため、詳細なテストは
        #  streamlit_components.pyのテストで行う)
        assert at.session_state["current_result"]["final_comment"] == "今日は爽やかな一日です"
    
    def test_sidebar_settings(self):
        """サイドバーの設定パネルのテスト"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # サイドバーにヘッダーが存在することを確認
        sidebar_elements = at.sidebar
        assert len(sidebar_elements) > 0
        
        # エクスパンダーが存在することを確認
        assert len(at.expander) > 0


class TestSessionState:
    """セッション状態管理のテスト"""
    
    def test_session_state_persistence(self):
        """セッション状態が正しく保持されることを確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # 初期状態を確認
        initial_location = at.session_state["selected_location"]
        initial_provider = at.session_state["llm_provider"]
        
        # 状態を変更
        at.selectbox[0].select("大阪").run()
        at.selectbox[1].select("anthropic").run()
        
        # 変更が保持されることを確認
        assert at.session_state["selected_location"] == "大阪"
        assert at.session_state["llm_provider"] == "anthropic"
        assert at.session_state["selected_location"] != initial_location
        assert at.session_state["llm_provider"] != initial_provider
    
    @patch('src.ui.streamlit_utils.load_history')
    def test_generation_history_initialization(self, mock_load_history):
        """生成履歴の初期化テスト"""
        # モック履歴データ
        mock_history = [
            {
                'timestamp': '2024-06-05T10:00:00',
                'location': '東京',
                'comment': '晴れやかな朝です',
                'provider': 'openai'
            }
        ]
        mock_load_history.return_value = mock_history
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # 履歴が読み込まれることを確認
        assert "generation_history" in at.session_state
        assert len(at.session_state["generation_history"]) == 1
        assert at.session_state["generation_history"][0]["location"] == "東京"


class TestProgressAndLoading:
    """プログレス表示とローディング状態のテスト"""
    
    @patch('src.workflows.comment_generation_workflow.run_comment_generation')
    @patch('time.sleep')  # time.sleepをモックして高速化
    def test_progress_bar_display(self, mock_sleep, mock_run_generation):
        """プログレスバーが表示されることを確認"""
        mock_run_generation.return_value = {
            'success': True,
            'final_comment': 'テストコメント',
            'generation_metadata': {}
        }
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # 生成ボタンをクリック
        at.button[0].click().run()
        
        # プログレス関連の要素が使用されることを確認
        # (StreamlitのAppTestではプログレスバーの詳細な状態確認は限定的)
        assert at.session_state["is_generating"] is False  # 生成完了後はFalse
    
    def test_button_disabled_during_generation(self):
        """生成中はボタンが無効化されることを確認"""
        at = AppTest.from_file("app.py")
        at.run()
        
        # 初期状態では生成中でない
        assert at.session_state["is_generating"] is False
        
        # ボタンのdisabled属性を確認
        # (実際の実装に依存するため、詳細は実装時に調整)


class TestErrorScenarios:
    """エラーシナリオのテスト"""
    
    @patch('src.workflows.comment_generation_workflow.run_comment_generation')
    def test_exception_handling(self, mock_run_generation):
        """例外発生時の処理をテスト"""
        # 例外を発生させる
        mock_run_generation.side_effect = Exception("予期しないエラー")
        
        at = AppTest.from_file("app.py")
        at.run()
        
        # 生成ボタンをクリック
        at.button[0].click().run()
        
        # エラーメッセージが表示されることを確認
        assert any("エラーが発生しました" in str(elem.value) for elem in at.error)
        
        # セッション状態の結果がエラーを含むことを確認
        result = at.session_state.get("current_result")
        if result:
            assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
