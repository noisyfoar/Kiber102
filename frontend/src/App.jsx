import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Auth from './pages/Auth'

export default function App() {
  return (
    <BrowserRouter>
      <main className="h-screen overflow-hidden bg-gradient-to-b from-slate-950 via-blue-950 to-slate-950 text-slate-100">
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top,_rgba(120,119,198,0.2),_transparent_60%)]" />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
