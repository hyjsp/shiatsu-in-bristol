import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import BookingsApp from './BookingsApp.jsx'

createRoot(document.getElementById('bookings-root')).render(
  <StrictMode>
    <BookingsApp />
  </StrictMode>,
)
