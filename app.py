"""
MobileCommentGenerator Streamlit UI

天気コメント生成システムのWebユーザーインターフェース
"""

import streamlit as st
from datetime import datetime
import json
import time
from typing import Dict, Any, Optional

from src.workflows.comment_generation_workflow import run_comment_generation
from src.ui.streamlit_components import (
    location_selector,
    llm_provider_selector,
    result_display,
    generation_history_display,
    settings_panel
)
from src.ui.streamlit_utils import (
    load_locations,
    copy_to_clipboard,
    save_to_history,
    load_history,
    format_timestamp
)

# ページ設定
st.set_page_config(
    page_title="天気コメント生成システム",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: #E3F2FD;
        border: 2px solid #1E88E5;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 1.5rem;
        text-align: center;
    }
    .copy-button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
    }
    .metadata-box {
        background-color: #F5F5F5;
        border-radius: 5px;
        padding: 1rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """セッション状態の初期化"""
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = load_history()
    
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = "東京"
    
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = "openai"
    
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    
    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False


def generate_comment_with_progress(location: str, llm_provider: str) -> Dict[str, Any]:
    """プログレスバー付きコメント生成"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 進捗更新のシミュレーション（実際のワークフローではコールバックを使用）
    progress_stages = [
        (0.2, "天気予報を取得中..."),
        (0.4, "過去コメントを検索中..."),
        (0.6, "類似コメントを選択中..."),
        (0.8, "コメントを生成中..."),
        (1.0, "完了！")
    ]
    
    try:
        # ワークフロー実行の開始
        st.session_state.is_generating = True
        
        # 各ステージで進捗更新（実際の実装では非同期処理）
        for progress, message in progress_stages[:-1]:
            progress_bar.progress(progress)
            status_text.text(message)
            time.sleep(0.5)  # デモ用の遅延
        
        # 実際のコメント生成
        result = run_comment_generation(
            location_name=location,
            target_datetime=datetime.now(),
            llm_provider=llm_provider
        )
        
        # 完了
        progress_bar.progress(1.0)
        status_text.text("完了！")
        time.sleep(0.5)
        
        # 履歴に保存
        if result['success']:
            save_to_history(result, location, llm_provider)
            st.session_state.generation_history = load_history()
        
        return result
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'final_comment': None
        }
    finally:
        st.session_state.is_generating = False
        progress_bar.empty()
        status_text.empty()


def main():
    """メインアプリケーション"""
    # セッション状態の初期化
    initialize_session_state()
    
    # ヘッダー
    st.markdown('<h1 class="main-header">☀️ 天気コメント生成システム ☀️</h1>', unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("設定")
        
        # APIキー設定
        with st.expander("APIキー設定", expanded=False):
            settings_panel()
        
        # 生成履歴
        st.header("生成履歴")
        generation_history_display(st.session_state.generation_history)
    
    # メインコンテンツ
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📍 入力設定")
        
        # 地点選択
        location = location_selector()
        st.session_state.selected_location = location
        
        # LLMプロバイダー選択
        llm_provider = llm_provider_selector()
        st.session_state.llm_provider = llm_provider
        
        # 現在時刻表示
        st.info(f"🕐 生成時刻: {format_timestamp(datetime.now())}")
        
        # 生成ボタン
        if st.button(
            "🎯 コメント生成",
            type="primary",
            disabled=st.session_state.is_generating,
            use_container_width=True
        ):
            with st.spinner("生成中..."):
                result = generate_comment_with_progress(location, llm_provider)
                st.session_state.current_result = result
                
                if result['success']:
                    st.success("✅ コメント生成が完了しました！")
                    st.balloons()
                else:
                    st.error(f"❌ 生成に失敗しました: {result.get('error', '不明なエラー')}")
    
    with col2:
        st.header("💬 生成結果")
        
        if st.session_state.current_result:
            result_display(st.session_state.current_result)
        else:
            st.info("👈 左側のパネルから地点とLLMプロバイダーを選択して、「コメント生成」ボタンをクリックしてください。")
            
            # サンプル表示
            with st.expander("サンプルコメント"):
                st.markdown("""
                **晴れの日**: 爽やかな朝ですね  
                **雨の日**: 傘をお忘れなく  
                **曇りの日**: 過ごしやすい一日です  
                **雪の日**: 足元にお気をつけて
                """)
    
    # フッター
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Version**: 1.0.0")
    with col2:
        st.markdown("**Last Updated**: 2025-06-06")
    with col3:
        st.markdown("**By**: WNI Team")


def run_streamlit_app():
    """Streamlitアプリケーションの実行"""
    main()


if __name__ == "__main__":
    run_streamlit_app()
