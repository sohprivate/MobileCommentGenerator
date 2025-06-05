# MobileSlack天気コメント - Project Instructions

## Project Overview
This is a Vue.js/Nuxt.js weather comment generation tool designed for Japanese users to create weather-related comments for Slack. The application integrates with weather APIs and generates contextual comments based on current weather conditions.

## Key Features
- **Location Selection**: Choose from major Japanese cities (東京, 大阪, 名古屋, 福岡, 札幌)
- **Weather Data Integration**: Fetches real-time weather data using coordinates
- **Comment Generation**: Creates weather-appropriate comments for Slack with multiple generation methods
- **Copy Functionality**: Easy copying of individual or all generated comments
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack
- **Framework**: Nuxt.js 3.17.5
- **Frontend**: Vue 3 with Composition API
- **Styling**: Scoped CSS with modern gradients and animations
- **Font**: Montserrat (Google Fonts)
- **API**: WxtechAPI for weather data (simulated)

## Component Structure

### Main Components
1. **LocationSelection.vue**: Location dropdown with data source information
2. **WeatherData.vue**: Coordinate input and weather data display
3. **GenerateSettings.vue**: Comment generation configuration
4. **GeneratedComment.vue**: Display and management of generated comments

### Color Scheme
- Primary Blue: `#0C419A`
- Secondary Blue: `#6BA2FC`  
- Success Green: `#28a745`
- Background Gradients: Various blue and purple combinations

## Development Guidelines

### Code Style
- Use Vue 3 Composition API with `<script setup>`
- Implement proper prop validation and emit declarations
- Use scoped CSS for component styling
- Follow responsive design principles with mobile-first approach

### Component Communication
- Parent-child communication via props and emits
- Event handling for user interactions (location changes, settings updates)
- Reactive data management with Vue's ref/reactive

### API Integration
- Weather data fetching (currently simulated)
- Error handling for API failures
- Loading states for better UX

### Responsive Design
- Grid layout for desktop (2-column)
- Stacked layout for mobile
- Proper breakpoints at 768px and 480px

## Future Enhancements
- Real weather API integration
- User preferences storage
- Comment history
- Export functionality
- Multi-language support
- Advanced weather data visualization

## Development Commands
```bash
npm install         # Install dependencies
npm run dev         # Start development server
npm run build       # Build for production
npm run generate    # Generate static site
```

## File Structure
```
├── app.vue                          # Main app layout
├── pages/
│   └── index.vue                   # Main page
├── components/
│   ├── LocationSelection.vue       # Location selector
│   ├── WeatherData.vue            # Weather data input
│   ├── GenerateSettings.vue       # Generation settings
│   └── GeneratedComment.vue       # Comment display
├── nuxt.config.ts                 # Nuxt configuration
└── package.json                   # Dependencies
```

## Design Principles
- Clean, modern Japanese UI design
- Intuitive user flow from location → weather → settings → generation
- Consistent color scheme and typography
- Smooth animations and transitions
- Accessible and user-friendly interface
