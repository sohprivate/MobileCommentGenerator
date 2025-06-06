# API Integration Guide for MobileSlack天気コメント

This document outlines the API endpoints and data formats needed for the Python backend to integrate with the frontend.

## Required Endpoints

### 1. Weather Data API

**Endpoint:** `/api/weather`

**Method:** GET

**Query Parameters:**
- `latitude` (number): Latitude coordinate
- `longitude` (number): Longitude coordinate

**Response Format:**
```json
{
  "temperature": 25.5,          // Current temperature in Celsius
  "condition": "sunny",         // Weather condition (sunny, cloudy, rainy, etc.)
  "humidity": 60,               // Humidity percentage
  "windSpeed": 5.2,             // Wind speed in m/s
  "precipitation": 0,           // Precipitation in mm
  "locationName": "東京",       // Location name
  "timestamp": "2025-06-05T12:00:00Z" // ISO timestamp
}
```

### 2. Comment Generation API

**Endpoint:** `/api/generate-comments`

**Method:** POST

**Request Body:**
```json
{
  "weatherData": {
    "temperature": 25.5,
    "condition": "sunny",
    "humidity": 60,
    "windSpeed": 5.2,
    "precipitation": 0,
    "locationName": "東京"
  },
  "settings": {
    "commentCount": 3,           // Number of comments to generate
    "commentStyle": "casual",    // Style of comments (casual, formal, etc.)
    "includeEmoji": true,        // Include emoji in comments
    "mentionWeather": true,      // Explicitly mention weather conditions
    "locale": "ja-JP"            // Language/locale
  }
}
```

**Response Format:**
```json
{
  "comments": [
    {
      "id": "c1",
      "text": "今日の東京は晴れで気温は25.5°Cです！素晴らしい一日になりそうですね！☀️",
      "timestamp": "2025-06-05T12:00:00Z"
    },
    {
      "id": "c2",
      "text": "東京の天気は最高ですね！外出するには絶好の日です！🌞",
      "timestamp": "2025-06-05T12:00:00Z"
    },
    {
      "id": "c3",
      "text": "こんにちは！今日の東京は25.5°Cの晴天です。良い一日をお過ごしください！😊",
      "timestamp": "2025-06-05T12:00:00Z"
    }
  ]
}
```

### 3. Location Data API

**Endpoint:** `/api/locations`

**Method:** GET

**Query Parameters:**
- `region` (string, optional): Filter locations by region

**Response Format:**
```json
{
  "locations": [
    {
      "id": "tokyo",
      "name": "東京",
      "region": "関東地方",
      "latitude": 35.6762,
      "longitude": 139.6503
    },
    {
      "id": "osaka",
      "name": "大阪",
      "region": "近畿地方",
      "latitude": 34.6937,
      "longitude": 135.5023
    },
    // Other locations...
  ]
}
```

## Error Handling

All API endpoints should return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found (resource not available)
- 500: Server Error

Error responses should follow this format:
```json
{
  "error": true,
  "message": "Error description message",
  "code": "ERROR_CODE"
}
```

## Authentication

The initial version will not require authentication, but consider adding API key validation in the future.

## CORS Configuration

Ensure the Python backend has CORS configured to allow requests from the frontend domain(s).
