# MobileSlack天気コメント Project

## Project Overview

MobileSlack天気コメント is a Vue.js/Nuxt.js weather comment generation tool designed for Japanese users to create weather-related comments for Slack. The application integrates with weather APIs and generates contextual comments based on current weather conditions.

This repository contains the frontend code and documentation for backend integration.

## For Backend Developers

This project requires a Python backend to:

1. Provide weather data based on location coordinates
2. Generate contextual Japanese weather comments for Slack
3. Serve location data for Japanese cities

## Important Documents

- **[API_INTEGRATION.md](./API_INTEGRATION.md)**: Detailed specification of required API endpoints
- **[BACKEND_SETUP.md](./BACKEND_SETUP.md)**: Step-by-step guide for setting up the Python backend

## Frontend Structure

The frontend is built with Nuxt.js 3.17.5 and Vue 3 using the Composition API. The main components are:

1. **LocationSelection.vue**: Location selection dropdown with filtering by region
2. **WeatherData.vue**: Weather data display with coordinate input
3. **GenerateSettings.vue**: Configuration for comment generation
4. **GeneratedComment.vue**: Display and management of generated comments

## Setting Up the Project

### Prerequisites

- Node.js (v18+)
- npm or yarn
- Python (v3.9+) for the backend

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Setup

See [BACKEND_SETUP.md](./BACKEND_SETUP.md) for detailed instructions.

## Integration Points

The frontend expects the following API endpoints:

1. `/api/weather` - Retrieve weather data by coordinates
2. `/api/generate-comments` - Generate weather-related comments
3. `/api/locations` - Get location data for Japanese cities

Detailed API specifications are available in [API_INTEGRATION.md](./API_INTEGRATION.md).

## Data Files

- `public/地点名.csv` - List of Japanese location names used by the application

## Next Steps

1. Review the API documentation
2. Set up the Python backend environment
3. Implement the required API endpoints
4. Test the integration between frontend and backend
5. Deploy the combined application

For any questions or issues, please contact [your-email@example.com].
