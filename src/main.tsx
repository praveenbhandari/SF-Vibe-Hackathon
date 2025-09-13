import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// Suppress React DevTools message and runtime errors
if (typeof window !== 'undefined') {
  // Handle runtime connection errors gracefully
  window.addEventListener('error', (event) => {
    if (event.message && event.message.includes('Could not establish connection')) {
      event.preventDefault();
      console.debug('Browser extension connection error suppressed');
    }
  });
  
  // Suppress unhandled promise rejections related to extensions
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && event.reason.message && event.reason.message.includes('Could not establish connection')) {
      event.preventDefault();
      console.debug('Extension connection promise rejection suppressed');
    }
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
