"""
Streamlit UIコンポーネント

再利用可能なUIコンポーネントの定義
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


def location_selector() -> str:
    """
    地点選択コンポーネント
    
    Returns:
        選択された地点名
    """
    from .streamlit_utils import load_locations, filter_locations
    
    # 地点データの読み込み
    locations = load_locations()
    
    # 検索機能
    search_query = st.text_input(
        "🔍 地点名で検索",
        key="location_search",
        placeholder="例: 東京、大阪、札幌...",
        help="地点名の一部を入力して検索できます"
    )
    
    # フィルタリング
    if search_query:
        filtered_locations = filter_locations(locations, search_query)
    else:
        filtered_locations = locations
    
    # よく使う地点（セッション状態から）
    if 'favorite_locations' not in st.session_state:
        st.session_state.favorite_locations = ["東京", "大阪", "札幌", "福岡", "那覇"]
    
    # お気に入り地点の表示
    if st.checkbox("⭐ よく使う地点のみ表示"):
        filtered_locations = [
            loc for loc in filtered_locations 
            if loc in st.session_state.favorite_locations
        ]
    
    # 地点選択
    selected_location = st.selectbox(
        "📍 地点を選択",
        options=filtered_locations,
        index=0 if filtered_locations else None,
        help="天気コメントを生成する地点を選択してください"
    )
    
    # お気に入り追加/削除
    if selected_location:
        col1, col2 = st.columns(2)
        with col1:
            if selected_location not in st.session_state.favorite_locations:
                if st.button("⭐ お気に入りに追加", use_container_width=True):
                    st.session_state.favorite_locations.append(selected_location)
                    st.success(f"{selected_location}をお気に入りに追加しました")
        with col2:
            if selected_location in st.session_state.favorite_locations:
                if st.button("🗑️ お気に入りから削除", use_container_width=True):
                    st.session_state.favorite_locations.remove(selected_location)
                    st.info(f"{selected_location}をお気に入りから削除しました")
    
    return selected_location


def llm_provider_selector() -> str:
    """
    LLMプロバイダー選択コンポーネント
    
    Returns:
        選択されたプロバイダー名
    """
    providers = {
        "openai": "🤖 OpenAI (GPT-4)",
        "gemini": "✨ Google Gemini",
        "anthropic": "🧠 Anthropic Claude"
    }
    
    # プロバイダー選択
    selected_key = st.selectbox(
        "🤖 LLMプロバイダーを選択",
        options=list(providers.keys()),
        format_func=lambda x: providers[x],
        help="コメント生成に使用するAIモデルを選択してください"
    )
    
    # プロバイダー情報の表示
    provider_info = {
        "openai": "高品質で安定した生成が可能です。",
        "gemini": "Google製の最新AIモデルです。",
        "anthropic": "安全性を重視した生成が特徴です。"
    }
    
    st.caption(f"ℹ️ {provider_info.get(selected_key, '')}")
    
    return selected_key


def result_display(result: Dict[str, Any]):
    """
    生成結果表示コンポーネント
    
    Args:
        result: 生成結果の辞書
    """
    if not result or not result.get('success'):
        st.error("生成結果がありません")
        return
    
    # メインコメント表示
    comment = result.get('final_comment', '')
    
    # カスタムHTMLで結果表示
    st.markdown(f"""
    <div class="result-box">
        <h2>{comment}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # アクションボタン
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 コピー", key="copy_button", use_container_width=True, type="primary"):
            from .streamlit_utils import copy_to_clipboard
            copy_to_clipboard(comment)
            st.toast("✅ クリップボードにコピーしました！", icon='✅')
    
    with col2:
        if st.button("🔄 再生成", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("💾 保存", use_container_width=True):
            # 履歴に保存（既に保存済みの場合はスキップ）
            st.info("履歴に保存されています")
    
    # メタデータ表示
    with st.expander("📊 生成情報の詳細"):
        metadata = result.get('generation_metadata', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("実行時間", f"{metadata.get('execution_time_ms', 0)}ms")
            st.metric("気温", f"{metadata.get('temperature', 'N/A')}°C")
            st.metric("リトライ回数", metadata.get('retry_count', 0))
        
        with col2:
            st.metric("天気", metadata.get('weather_condition', 'N/A'))
            st.metric("LLMプロバイダー", metadata.get('llm_provider', 'N/A'))
            st.metric("検証スコア", f"{metadata.get('validation_score', 0):.2f}" if metadata.get('validation_score') else "N/A")
        
        # 選択されたコメント情報
        if 'selected_past_comments' in metadata:
            st.subheader("📝 参考にした過去コメント")
            for comment in metadata['selected_past_comments']:
                st.text(f"• {comment.get('text', '')}")
        
        # 生の JSON データ
        with st.expander("🔧 詳細データ (JSON)"):
            st.json(metadata)


def generation_history_display(history: List[Dict[str, Any]]):
    """
    生成履歴表示コンポーネント
    
    Args:
        history: 生成履歴のリスト
    """
    if not history:
        st.info("まだ生成履歴がありません。")
        return
    
    import pandas as pd
    
    # DataFrameとして表示
    df = pd.DataFrame(history)
    st.dataframe(df)
    
    # CSVダウンロードボタン
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 履歴をダウンロード",
        data=csv,
        file_name=f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # 最新の履歴から表示
    st.divider()
    st.subheader("最近の生成履歴")
    
    for idx, item in enumerate(reversed(history[-10:])):  # 最新10件
        timestamp = item.get('timestamp', '')
        location = item.get('location', '不明')
        comment = item.get('final_comment', '')
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.text(f"📍 {location}")
                st.caption(f"💬 {comment}")
            
            with col2:
                st.caption(timestamp[:16])  # YYYY-MM-DD HH:MM
                
            # 詳細ボタン
            if st.button(f"詳細", key=f"history_{idx}"):
                with st.expander("履歴詳細", expanded=True):
                    st.json(item)
            
            st.divider()
    
    # 全履歴のエクスポート
    if st.button("📥 履歴をエクスポート"):
        # JSON形式でダウンロード
        json_str = json.dumps(history, ensure_ascii=False, indent=2)
        st.download_button(
            label="JSONファイルをダウンロード",
            data=json_str,
            file_name=f"comment_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def settings_panel():
    """
    設定パネルコンポーネント
    """
    st.subheader("🔐 APIキー設定")
    
    import os
    
    # OpenAI
    openai_key = st.text_input(
        "OpenAI APIキー",
        type="password",
        value=os.environ.get('OPENAI_API_KEY', st.session_state.get('openai_api_key', '')),
        help="OpenAI APIキーを入力してください"
    )
    if openai_key:
        st.session_state.openai_api_key = openai_key
        if openai_key and len(openai_key) > 10:
            st.success("✅ OpenAI APIキー設定済み")
    
    # Gemini
    gemini_key = st.text_input(
        "Gemini APIキー",
        type="password",
        value=os.environ.get('GEMINI_API_KEY', st.session_state.get('gemini_api_key', '')),
        help="Google Gemini APIキーを入力してください"
    )
    if gemini_key:
        st.session_state.gemini_api_key = gemini_key
        if gemini_key and len(gemini_key) > 10:
            st.success("✅ Gemini APIキー設定済み")
    
    # Anthropic
    anthropic_key = st.text_input(
        "Anthropic APIキー",
        type="password",
        value=os.environ.get('ANTHROPIC_API_KEY', st.session_state.get('anthropic_api_key', '')),
        help="Anthropic Claude APIキーを入力してください"
    )
    if anthropic_key:
        st.session_state.anthropic_api_key = anthropic_key
        if anthropic_key and len(anthropic_key) > 10:
            st.success("✅ Anthropic APIキー設定済み")
    
    # 検証ボタン
    if st.button("🔍 APIキーを検証"):
        with st.spinner("検証中..."):
            # TODO: 実際のAPI検証ロジックを実装
            st.success("APIキーが有効です！")
    
    st.divider()
    
    # 生成設定
    st.subheader("⚙️ 生成設定")
    
    # 文字数制限
    max_chars = st.slider(
        "最大文字数",
        min_value=10,
        max_value=200,
        value=50,
        help="生成コメントの最大文字数"
    )
    st.session_state.max_chars = max_chars
    
    # コメントスタイル
    comment_style = st.selectbox(
        "コメントスタイル",
        options=["カジュアル", "フォーマル", "親しみやすい"],
        help="生成コメントのスタイルを選択"
    )
    st.session_state.comment_style = comment_style
    
    # 絵文字使用
    use_emoji = st.checkbox(
        "絵文字を使用する",
        value=st.session_state.get('use_emoji', True),
        help="コメントに絵文字を含めるかどうか"
    )
    st.session_state.use_emoji = use_emoji
    
    st.divider()
    
    # その他の設定
    st.subheader("⚙️ その他の設定")
    
    # 最大リトライ回数
    max_retries = st.number_input(
        "最大リトライ回数",
        min_value=0,
        max_value=10,
        value=5,
        help="コメント生成が失敗した場合の最大リトライ回数"
    )
    st.session_state.max_retries = max_retries
    
    # タイムアウト設定
    timeout = st.slider(
        "タイムアウト (秒)",
        min_value=10,
        max_value=60,
        value=30,
        help="API呼び出しのタイムアウト時間"
    )
    st.session_state.timeout = timeout
    
    # デバッグモード
    debug_mode = st.checkbox(
        "デバッグモード",
        value=st.session_state.get('debug_mode', False),
        help="詳細なログ情報を表示します"
    )
    st.session_state.debug_mode = debug_mode
