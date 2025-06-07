# Backend Developer Setup Guide

This document provides instructions for setting up and connecting the Python backend to the MobileSlack天気コメント frontend.

## Project Overview

MobileSlack天気コメント is a Vue.js/Nuxt.js weather comment generation tool designed for Japanese users to create weather-related comments for Slack. The application integrates with weather APIs and generates contextual comments based on current weather conditions.

## Frontend Structure

The frontend is built with Nuxt.js 3.17.5 and Vue 3 using the Composition API. The key components are:

1. **LocationSelection.vue**: Handles selection of Japanese cities/regions
2. **WeatherData.vue**: Displays weather data based on coordinates
3. **GenerateSettings.vue**: Configures comment generation parameters
4. **GeneratedComment.vue**: Displays and manages generated comments

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Create Python Backend

Create a new Python project for the backend. Recommended structure:

```
backend/
├── app.py              # Main application file (Flask/FastAPI)
├── requirements.txt    # Python dependencies
├── weather/            # Weather service module
│   ├── __init__.py
│   ├── service.py      # Weather API integration
│   └── models.py       # Data models
├── comment_generator/  # Comment generation module
│   ├── __init__.py
│   ├── generator.py    # Comment generation logic
│   └── templates.py    # Comment templates
└── data/
    └── locations.csv   # Location data
```

### 4. Install Required Python Packages

Recommended packages:

```
# requirements.txt
fastapi==0.100.0        # API framework
uvicorn==0.22.0         # ASGI server
requests==2.30.0        # HTTP client for weather API
pandas==2.0.3           # Data processing
pydantic==2.0.3         # Data validation
python-dotenv==1.0.0    # Environment variable management
jinja2==3.1.2           # Template engine for comment generation
```

Install with:
```bash
pip install -r requirements.txt
```

### 5. Implement API Endpoints

Implement the API endpoints as specified in the `API_INTEGRATION.md` document. Here's a simple FastAPI example:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="MobileSlack天気コメント API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class WeatherData(BaseModel):
    temperature: float
    condition: str
    humidity: int
    windSpeed: float
    precipitation: float
    locationName: str

class GenerationSettings(BaseModel):
    commentCount: int
    commentStyle: str
    includeEmoji: bool
    mentionWeather: bool
    locale: str = "ja-JP"

class CommentRequest(BaseModel):
    weatherData: WeatherData
    settings: GenerationSettings

class Comment(BaseModel):
    id: str
    text: str
    timestamp: str

class CommentResponse(BaseModel):
    comments: List[Comment]

# API endpoints
@app.get("/api/weather")
async def get_weather(latitude: float, longitude: float):
    # Implement weather data retrieval here
    # ...
    
    return {
        "temperature": 25.5,
        "condition": "sunny",
        "humidity": 60,
        "windSpeed": 5.2,
        "precipitation": 0,
        "locationName": "東京",
        "timestamp": "2025-06-05T12:00:00Z"
    }

@app.post("/api/generate-comments", response_model=CommentResponse)
async def generate_comments(request: CommentRequest):
    # Implement comment generation here
    # ...
    
    return {
        "comments": [
            {
                "id": "c1",
                "text": f"今日の{request.weatherData.locationName}は{request.weatherData.condition}で気温は{request.weatherData.temperature}°Cです！素晴らしい一日になりそうですね！☀️",
                "timestamp": "2025-06-05T12:00:00Z"
            },
            # Add more generated comments...
        ]
    }

@app.get("/api/locations")
async def get_locations(region: Optional[str] = None):
    # Implement location data retrieval here
    # ...
    
    locations = [
        {
            "id": "tokyo",
            "name": "東京",
            "region": "関東地方",
            "latitude": 35.6762,
            "longitude": 139.6503
        },
        # Add more locations...
    ]
    
    if region:
        locations = [loc for loc in locations if loc["region"] == region]
        
    return {"locations": locations}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

### 6. Connect Frontend to Backend

Update the Nuxt.js configuration to connect to your Python backend:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  
  // Add runtime config for API base URL
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000'
    }
  }
})
```

### 7. Test the Integration

1. Start the Python backend:
```bash
cd backend
uvicorn app:app --reload
```

2. Start the Nuxt.js frontend:
```bash
npm run dev
```

3. Open the frontend in your browser and test the integration.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nuxt.js Documentation](https://nuxt.com/docs)
- [Weather API Documentation](https://your-weather-api-provider.com/docs)

## Contact

For any questions or issues, please contact [your-email@example.com].
