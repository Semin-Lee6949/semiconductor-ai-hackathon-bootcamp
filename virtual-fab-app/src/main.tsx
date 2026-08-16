import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

const isLegacyPublicAddress = window.location.hostname === 'waterfirst.pro' && window.location.protocol !== 'https:'

if (isLegacyPublicAddress) {
  const destination = `https://waterfirst.pro/virtual-fab/${window.location.search}${window.location.hash}`
  window.location.replace(destination)
} else {
  createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
}
