# Streamlit バックエンド統合ガイド

このドキュメントでは、Nuxt 3フロントエンドとStreamlitバックエンドの統合方法について説明します。

## 概要

フロントエンドは以下のAPIエンドポイントを期待しています：

- `GET /api/locations` - 地点データの取得
- `POST /api/weather` - 天気データの取得
- `POST /api/generate-comments` - コメント生成

## バックエンド実装要件

### 1. Streamlit + FastAPI 構成

Streamlitアプリケーション内でFastAPIを使用してAPIエンドポイントを提供する必要があります。

```python
# src/api_server.py
import streamlit as st
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from threading import Thread
import pandas as pd
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Nuxt開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class Location(BaseModel):
    name: str
    latitude: float
    longitude: float
    area: Optional[str] = None

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    target_time: str = "12h"  # "12h" or "24h"

class WeatherData(BaseModel):
    location: str
    temperature: Optional[float]
    humidity: Optional[float]
    windSpeed: Optional[float]
    precipitation: Optional[float]
    weatherCondition: Optional[str]
    timestamp: str

class GenerateRequest(BaseModel):
    locations: List[str]
    settings: dict
    weather_data: Optional[WeatherData] = None

class GeneratedComment(BaseModel):
    id: str
    text: str
    location: Optional[str]
    timestamp: str
    weather: Optional[WeatherData]

# エンドポイント
@app.get("/api/locations", response_model=List[Location])
async def get_locations():
    """Chiten.csvから地点データを読み込んで返す"""
    try:
        df = pd.read_csv("Chiten.csv")
        locations = []
        for _, row in df.iterrows():
            locations.append(Location(
                name=row["地点名"],
                latitude=row.get("緯度", 0),
                longitude=row.get("経度", 0),
                area=row.get("地方", None)
            ))
        return locations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weather", response_model=WeatherData)
async def get_weather(request: WeatherRequest):
    """WxTech APIから天気データを取得"""
    # TODO: 実際のWxTech API実装
    # ここではモックデータを返す
    return WeatherData(
        location=f"緯度{request.latitude}, 経度{request.longitude}",
        temperature=22.5,
        humidity=65,
        windSpeed=3.2,
        weatherCondition="晴れ",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/generate-comments", response_model=List[GeneratedComment])
async def generate_comments(request: GenerateRequest):
    """LangGraphを使用してコメントを生成"""
    # TODO: LangGraphパイプラインの実装
    # ここではモックデータを返す
    comments = []
    for i, location in enumerate(request.locations):
        comments.append(GeneratedComment(
            id=f"comment-{i}",
            text=f"{location}は晴れて過ごしやすい一日になりそうです。",
            location=location,
            timestamp=datetime.now().isoformat(),
            weather=request.weather_data
        ))
    return comments

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# FastAPIサーバーを別スレッドで起動
def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Streamlitアプリケーション
def main():
    st.title("MobileComment Generator Backend")
    
    # API サーバーを起動
    if "api_started" not in st.session_state:
        thread = Thread(target=run_api, daemon=True)
        thread.start()
        st.session_state.api_started = True
        st.success("API server started on http://localhost:8000")
    
    # Streamlit UI
    st.write("Backend is running...")

if __name__ == "__main__":
    main()
```

### 2. LangGraph パイプライン統合

```python
# src/langgraph_pipeline.py
from langgraph import StateGraph, State
from typing import List, Dict, Any
import openai
from dataclasses import dataclass

@dataclass
class CommentGenerationState(State):
    locations: List[str]
    weather_data: Dict[str, Any]
    settings: Dict[str, Any]
    past_comments: List[Dict[str, str]]
    generated_comments: List[str]
    
def fetch_past_comments(state: CommentGenerationState) -> CommentGenerationState:
    """S3から過去のコメントを取得"""
    # TODO: S3アクセス実装
    return state

def select_comment_pairs(state: CommentGenerationState) -> CommentGenerationState:
    """条件に合うコメントペアを選択"""
    # TODO: 選択ロジック実装
    return state

def generate_with_llm(state: CommentGenerationState) -> CommentGenerationState:
    """LLMを使用してコメント生成"""
    # TODO: OpenAI/Gemini/Anthropic API実装
    return state

def validate_comments(state: CommentGenerationState) -> CommentGenerationState:
    """生成されたコメントのルールチェック"""
    # TODO: バリデーション実装
    return state

# グラフの構築
def create_comment_generation_graph():
    graph = StateGraph(CommentGenerationState)
    
    # ノードの追加
    graph.add_node("fetch_past", fetch_past_comments)
    graph.add_node("select_pairs", select_comment_pairs)
    graph.add_node("generate", generate_with_llm)
    graph.add_node("validate", validate_comments)
    
    # エッジの定義
    graph.add_edge("fetch_past", "select_pairs")
    graph.add_edge("select_pairs", "generate")
    graph.add_edge("generate", "validate")
    
    return graph.compile()
```

### 3. 環境変数設定

```bash
# .env
# WxTech API
WXTECH_API_KEY=your_wxtech_api_key

# LLM API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=it-literacy-457604437098-ap-northeast-1

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

## フロントエンド使用方法

### 1. 環境設定

```bash
cd src/tool_design
cp .env.example .env
# NUXT_PUBLIC_API_BASE_URL=http://localhost:8000 を設定
```

### 2. 開発サーバー起動

```bash
# バックエンド起動
cd src
streamlit run api_server.py

# フロントエンド起動（別ターミナル）
cd src/tool_design
npm install
npm run dev
```

### 3. APIレスポンス形式

#### 地点データ
```json
[
  {
    "name": "東京",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "area": "関東地方"
  }
]
```

#### 天気データ
```json
{
  "location": "東京",
  "temperature": 22.5,
  "humidity": 65,
  "windSpeed": 3.2,
  "weatherCondition": "晴れ",
  "timestamp": "2025-06-06T12:00:00Z"
}
```

#### 生成されたコメント
```json
[
  {
    "id": "comment-1",
    "text": "東京は晴れて過ごしやすい一日になりそうです。",
    "location": "東京",
    "timestamp": "2025-06-06T12:00:00Z",
    "weather": {
      "temperature": 22.5,
      "humidity": 65
    }
  }
]
```

## デプロイメント

### AWS EC2/ECS デプロイ

1. Dockerイメージの作成
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["streamlit", "run", "api_server.py"]
```

2. docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      
  frontend:
    build: ./src/tool_design
    ports:
      - "3000:3000"
    environment:
      - NUXT_PUBLIC_API_BASE_URL=http://backend:8000
    depends_on:
      - backend
```

## トラブルシューティング

### CORS エラー
- バックエンドのCORS設定でフロントエンドのURLを許可しているか確認
- 開発環境では `http://localhost:3000` を許可

### API接続エラー
- バックエンドが起動しているか確認（http://localhost:8000/health）
- 環境変数 `NUXT_PUBLIC_API_BASE_URL` が正しく設定されているか確認

### データ取得エラー
- `Chiten.csv` ファイルが正しい場所に配置されているか確認
- S3バケットへのアクセス権限があるか確認