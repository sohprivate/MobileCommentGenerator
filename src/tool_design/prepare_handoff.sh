#!/bin/zsh

# Script to prepare the MobileSlack天気コメント project for backend handoff

echo "Preparing MobileSlack天気コメント for backend handoff..."

# Current directory
PROJECT_DIR="$(pwd)"
echo "Working in: $PROJECT_DIR"

# Create a handoff directory
HANDOFF_DIR="$PROJECT_DIR/frontend-handoff"
mkdir -p "$HANDOFF_DIR"

# Essential directories to copy
mkdir -p "$HANDOFF_DIR/components"
mkdir -p "$HANDOFF_DIR/pages"
mkdir -p "$HANDOFF_DIR/public"
mkdir -p "$HANDOFF_DIR/assets"

# Copy essential files
echo "Copying essential files..."
cp app.vue "$HANDOFF_DIR/"
cp nuxt.config.ts "$HANDOFF_DIR/"
cp package.json "$HANDOFF_DIR/"
cp tsconfig.json "$HANDOFF_DIR/"

# Copy components
cp components/*.vue "$HANDOFF_DIR/components/"

# Copy pages
cp pages/*.vue "$HANDOFF_DIR/pages/"

# Copy public assets
cp -r public/* "$HANDOFF_DIR/public/"

# Copy assets if they exist and are needed
if [ -d "assets" ]; then
  cp -r assets/* "$HANDOFF_DIR/assets/"
fi

# Copy documentation
cp API_INTEGRATION.md "$HANDOFF_DIR/"
cp BACKEND_SETUP.md "$HANDOFF_DIR/"

# Create a README for the handoff
cat > "$HANDOFF_DIR/README.md" << 'EOF'
# MobileSlack天気コメント Frontend Handoff

This directory contains the essential frontend files for the MobileSlack天気コメント project.

## Contents

- **Frontend Code**: Vue.js/Nuxt.js components and pages
- **API Integration Guide**: Documentation on required API endpoints (see API_INTEGRATION.md)
- **Backend Setup Guide**: Instructions for setting up the Python backend (see BACKEND_SETUP.md)

## Setup Instructions

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

## Backend Integration

Refer to the BACKEND_SETUP.md file for detailed instructions on setting up and connecting the Python backend.

## Project Structure

- `components/`: UI components
- `pages/`: Page layouts
- `public/`: Static assets
- `assets/`: CSS and other assets
- `nuxt.config.ts`: Nuxt.js configuration
- `package.json`: Dependencies and scripts

## Contact

For any questions or issues with the frontend code, please contact [your-email@example.com].
EOF

echo "Project prepared for handoff at: $HANDOFF_DIR"
echo "Next steps:"
echo "1. Review the handoff directory to ensure all necessary files are included"
echo "2. Share the handoff directory with the backend developer"
echo "3. Provide any additional context or instructions as needed"
