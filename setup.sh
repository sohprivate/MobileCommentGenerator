#!/bin/bash
# Mobile Comment Generator - 自動セットアップスクリプト
# Usage: ./setup.sh [dev|prod]

set -e  # エラー時に停止

# カラーコード
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Python バージョンチェック
check_python() {
    log_info "Python バージョンをチェック中..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python が見つかりません。Python 3.10以上をインストールしてください。"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION を検出"
}

# uv のインストール確認
check_uv() {
    log_info "uv の確認中..."
    
    if ! command -v uv &> /dev/null; then
        log_warning "uv が見つかりません。インストール中..."
        
        # セキュリティ強化: インストールスクリプトを検証
        INSTALL_SCRIPT="/tmp/uv-install-$$.sh"
        curl -LsSf https://astral.sh/uv/install.sh -o "$INSTALL_SCRIPT"
        
        # インストールスクリプトが正常にダウンロードされたか確認
        if [ ! -f "$INSTALL_SCRIPT" ] || [ ! -s "$INSTALL_SCRIPT" ]; then
            log_error "uv インストールスクリプトのダウンロードに失敗しました"
            exit 1
        fi
        
        # インストール実行
        sh "$INSTALL_SCRIPT"
        rm -f "$INSTALL_SCRIPT"
        
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if ! command -v uv &> /dev/null; then
            log_error "uv のインストールに失敗しました"
            exit 1
        fi
    fi
    
    UV_VERSION=$(uv --version)
    log_success "uv を検出: $UV_VERSION"
}

# 仮想環境の作成
setup_venv() {
    log_info "仮想環境をセットアップ中..."
    
    # 既存の仮想環境を削除
    if [ -d ".venv" ]; then
        log_warning "既存の仮想環境を削除中..."
        rm -rf .venv
    fi
    
    # 新しい仮想環境作成（検出されたPythonバージョンを使用）
    uv venv --python $PYTHON_CMD
    log_success "仮想環境を作成しました"
}

# 依存関係のインストール
install_dependencies() {
    local MODE=${1:-"dev"}
    
    log_info "依存関係をインストール中... (モード: $MODE)"
    
    # 基本依存関係
    uv pip install -r requirements.txt
    
    if [ "$MODE" = "dev" ]; then
        # 開発用依存関係
        uv pip install -r requirements-dev.txt
        log_success "開発用依存関係をインストールしました"
    else
        log_success "本番用依存関係をインストールしました"
    fi
}

# 環境変数ファイルの設定
setup_env() {
    log_info "環境変数ファイルをセットアップ中..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success ".env ファイルを作成しました"
            log_warning "⚠️  .env ファイルでAPIキーを設定してください"
        else
            log_warning ".env.example が見つかりません"
        fi
    else
        log_info ".env ファイルは既に存在します"
    fi
}

# インストール確認
verify_installation() {
    log_info "インストールを確認中..."
    
    # 仮想環境有効化
    source .venv/bin/activate
    
    # 主要パッケージの確認
    python -c "import langgraph; print(f'✓ LangGraph: {langgraph.__version__}')" 2>/dev/null || log_warning "LangGraph の確認に失敗"
    python -c "import streamlit; print(f'✓ Streamlit: {streamlit.__version__}')" 2>/dev/null || log_warning "Streamlit の確認に失敗"
    python -c "import boto3; print(f'✓ Boto3: {boto3.__version__}')" 2>/dev/null || log_warning "Boto3 の確認に失敗"
    python -c "import openai; print(f'✓ OpenAI: {openai.__version__}')" 2>/dev/null || log_warning "OpenAI の確認に失敗"
    
    log_success "パッケージ確認完了"
}

# メイン処理
main() {
    local MODE=${1:-"dev"}
    
    echo "🚀 Mobile Comment Generator セットアップ"
    echo "モード: $MODE"
    echo "=================================="
    
    check_python
    check_uv
    setup_venv
    install_dependencies $MODE
    setup_env
    verify_installation
    
    echo ""
    echo "🎉 セットアップ完了！"
    echo ""
    echo "次のステップ:"
    echo "1. 仮想環境を有効化: source .venv/bin/activate"
    echo "2. .env ファイルでAPIキーを設定"
    echo "3. アプリケーション起動: streamlit run app.py"
    echo ""
}

# スクリプト実行
main "$@"