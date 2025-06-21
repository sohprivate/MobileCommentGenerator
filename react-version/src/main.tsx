import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/global.css'
import { themeClass } from './styles/theme.css'
import App from './App.tsx'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Root element not found')
rootElement.classList.add(themeClass)

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
