"""
Streamlitコンポーネントのテスト

UIコンポーネント関数の個別テスト
"""

import pytest
from unittest.mock import patch, MagicMock, call
import streamlit as st
from datetime import datetime

# テスト対象のインポート
from src.ui.streamlit_components import (
    location_selector,
    llm_provider_selector,
    result_display,
    generation_history_display,
    settings_panel
)


class TestLocationSelector:
    """地点選択コンポーネントのテスト"""
    
    @patch('streamlit.selectbox')
    @patch('src.ui.streamlit_utils.load_locations')
    def test_location_selector_basic(self, mock_load_locations, mock_selectbox):
        """基本的な地点選択機能のテスト"""
        # モックデータ
        mock_locations = ["東京", "大阪", "稚内", "那覇"]
        mock_load_locations.return_value = mock_locations
        mock_selectbox.return_value = "東京"
        
        # 実行
        result = location_selector()
        
        # 検証
        mock_load_locations.assert_called_once()
        mock_selectbox.assert_called_once()
        assert result == "東京"
        
        # selectboxの引数を確認
        args, kwargs = mock_selectbox.call_args
        assert args[0] == "📍 地点を選択"
        assert set(kwargs.get('options', [])) == set(mock_locations)
    
    @patch('streamlit.checkbox')
    @patch('streamlit.text_input')
    @patch('streamlit.selectbox')
    @patch('src.ui.streamlit_utils.load_locations')
    @patch('src.ui.streamlit_utils.filter_locations')
    def test_location_selector_with_search(
        self, mock_filter, mock_load_locations, mock_selectbox, mock_text_input, mock_checkbox
    ):
        """検索機能付き地点選択のテスト"""
        # モックデータ
        all_locations = ["東京", "大阪", "京都", "東大阪"]
        filtered_locations = ["東京", "東大阪"]
        mock_load_locations.return_value = all_locations
        mock_text_input.return_value = "東"
        mock_filter.return_value = filtered_locations
        mock_selectbox.return_value = "東京"
        mock_checkbox.return_value = False  # お気に入りのみ表示をオフ
        
        # 実行
        result = location_selector()
        
        # 検証
        mock_text_input.assert_called_once_with("🔍 地点名で検索", key="location_search")
        mock_filter.assert_called_once_with(all_locations, "東")
        
        # フィルタされた結果がselectboxに渡されることを確認
        args, kwargs = mock_selectbox.call_args
        assert set(kwargs.get('options', [])) == set(filtered_locations)


class TestLLMProviderSelector:
    """LLMプロバイダー選択コンポーネントのテスト"""
    
    @patch('streamlit.selectbox')
    def test_llm_provider_selector(self, mock_selectbox):
        """LLMプロバイダー選択のテスト"""
        mock_selectbox.return_value = "openai"
        
        result = llm_provider_selector()
        
        # 検証
        mock_selectbox.assert_called_once()
        args, kwargs = mock_selectbox.call_args
        assert args[0] == "🤖 LLMプロバイダーを選択"
        assert "openai" in kwargs.get('options', [])
        assert "gemini" in kwargs.get('options', [])
        assert "anthropic" in kwargs.get('options', [])
        assert result == "openai"


class TestResultDisplay:
    """結果表示コンポーネントのテスト"""
    
    @patch('streamlit.markdown')
    @patch('streamlit.success')
    @patch('streamlit.button')
    @patch('streamlit.expander')
    @patch('streamlit.json')
    def test_result_display_success(
        self, mock_json, mock_expander, mock_button, mock_success, mock_markdown
    ):
        """成功時の結果表示テスト"""
        # モック結果データ
        result = {
            'success': True,
            'final_comment': '今日は爽やかな一日です',
            'generation_metadata': {
                'location_name': '東京',
                'weather_condition': '晴れ',
                'temperature': 25.0,
                'execution_time_ms': 1500,
                'retry_count': 0
            }
        }
        
        # expanderのモック設定
        mock_expander_context = MagicMock()
        mock_expander.return_value.__enter__ = MagicMock(return_value=mock_expander_context)
        mock_expander.return_value.__exit__ = MagicMock(return_value=None)
        
        # コピーボタンのモック
        mock_button.return_value = False  # ボタンがクリックされていない
        
        # 実行
        result_display(result)
        
        # 検証
        mock_markdown.assert_called()
        # コメントが表示されることを確認
        markdown_calls = [call[0][0] for call in mock_markdown.call_args_list]
        assert any('今日は爽やかな一日です' in str(call) for call in markdown_calls)
        
        # コピーボタンが表示されることを確認
        mock_button.assert_called_with("📋 コピー", key="copy_button")
        
        # 詳細情報のexpanderが作成されることを確認
        mock_expander.assert_called_with("📊 詳細情報")
    
    @patch('streamlit.markdown')
    @patch('streamlit.button')
    @patch('streamlit.toast')
    @patch('src.ui.streamlit_utils.copy_to_clipboard')
    def test_result_display_copy_button(
        self, mock_copy, mock_toast, mock_button, mock_markdown
    ):
        """コピーボタンのテスト"""
        result = {
            'success': True,
            'final_comment': 'テストコメント',
            'generation_metadata': {}
        }
        
        # ボタンがクリックされた場合
        mock_button.return_value = True
        mock_copy.return_value = True
        
        # 実行
        result_display(result)
        
        # 検証
        mock_copy.assert_called_once_with('テストコメント')
        mock_toast.assert_called_once_with("✅ クリップボードにコピーしました！", icon='✅')
    
    @patch('streamlit.error')
    def test_result_display_empty(self, mock_error):
        """空の結果の場合のテスト"""
        result_display({})
        mock_error.assert_called_once_with("生成結果がありません")


class TestGenerationHistoryDisplay:
    """生成履歴表示コンポーネントのテスト"""
    
    @patch('streamlit.dataframe')
    @patch('pandas.DataFrame')
    def test_history_display_with_data(self, mock_df, mock_dataframe):
        """履歴データがある場合の表示テスト"""
        history = [
            {
                'timestamp': '2024-06-05T10:00:00',
                'location': '東京',
                'comment': '晴れやかな朝です',
                'provider': 'openai'
            },
            {
                'timestamp': '2024-06-05T11:00:00',
                'location': '大阪',
                'comment': '雨が降っています',
                'provider': 'gemini'
            }
        ]
        
        # DataFrameのモック
        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance
        
        # 実行
        generation_history_display(history)
        
        # 検証
        mock_df.assert_called_once_with(history)
        mock_dataframe.assert_called_once()
    
    @patch('streamlit.info')
    def test_history_display_empty(self, mock_info):
        """履歴が空の場合のテスト"""
        generation_history_display([])
        mock_info.assert_called_once_with("まだ生成履歴がありません。")
    
    @patch('streamlit.dataframe')
    @patch('streamlit.button')
    @patch('streamlit.download_button')
    @patch('pandas.DataFrame')
    def test_history_export_button(
        self, mock_df, mock_download, mock_button, mock_dataframe
    ):
        """履歴エクスポートボタンのテスト"""
        history = [{'timestamp': '2024-06-05', 'comment': 'test'}]
        
        # DataFrameのモック
        mock_df_instance = MagicMock()
        mock_df_instance.to_csv.return_value = "timestamp,comment\n2024-06-05,test"
        mock_df.return_value = mock_df_instance
        
        # 実行
        generation_history_display(history)
        
        # エクスポートボタンが表示されることを確認
        assert any(
            call for call in mock_download.call_args_list 
            if "履歴をダウンロード" in str(call)
        )


class TestSettingsPanel:
    """設定パネルのテスト"""
    
    @patch('streamlit.text_input')
    @patch('streamlit.checkbox')
    @patch('streamlit.success')
    @patch('streamlit.error')
    @patch('os.environ.get')
    def test_settings_panel_api_keys(
        self, mock_env_get, mock_error, mock_success, 
        mock_checkbox, mock_text_input
    ):
        """APIキー設定のテスト"""
        # 環境変数のモック
        mock_env_get.side_effect = lambda key, default=None: {
            'OPENAI_API_KEY': 'test-openai-key',
            'GEMINI_API_KEY': '',
            'ANTHROPIC_API_KEY': None
        }.get(key, default)
        
        # テキスト入力のモック
        mock_text_input.side_effect = [
            'test-openai-key',  # OpenAI
            '',                 # Gemini
            ''                  # Anthropic
        ]
        
        # 実行
        settings_panel()
        
        # APIキー入力フィールドが作成されることを確認
        assert mock_text_input.call_count >= 3
        
        # 成功メッセージが表示されることを確認（OpenAIキーが設定済み）
        success_calls = [call[0][0] for call in mock_success.call_args_list]
        assert any("OpenAI" in str(call) and "設定済み" in str(call) for call in success_calls)
    
    @patch('streamlit.subheader')
    @patch('streamlit.slider')
    @patch('streamlit.selectbox')
    @patch('streamlit.checkbox')
    def test_settings_panel_generation_settings(
        self, mock_checkbox, mock_selectbox, mock_slider, mock_subheader
    ):
        """生成設定パネルのテスト"""
        # 実行
        settings_panel()
        
        # 生成設定のサブヘッダーが表示されることを確認
        subheader_calls = [call[0][0] for call in mock_subheader.call_args_list]
        assert any("生成設定" in str(call) for call in subheader_calls)
        
        # スライダーが使用されることを確認（文字数制限など）
        assert mock_slider.call_count > 0
        
        # セレクトボックスが使用されることを確認（スタイル選択など）
        assert mock_selectbox.call_count > 0
        
        # チェックボックスが使用されることを確認（絵文字使用など）
        assert mock_checkbox.call_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
