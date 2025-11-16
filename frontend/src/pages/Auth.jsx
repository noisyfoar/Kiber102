import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthForm from '../components/AuthForm'
import { api, setAuthToken } from '../services/api'

const BENEFITS = [
  {
    title: 'Единый кабинет',
    text: 'Сохраняем историю интерпретаций и персональные подсказки на всех устройствах.'
  },
  {
    title: 'Голос и текст',
    text: 'Переходи между форматами общения в любой момент без потери контекста.'
  },
  {
    title: 'Эмоциональная аналитика',
    text: 'ИИ отслеживает настроение сна и предлагает практику для осознанного пробуждения.'
  }
]

export default function Auth() {
  const [mode, setMode] = useState('login') // 'login' или 'register'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const handleLogin = async (form) => {
    try {
      setLoading(true)
      setError(null)
      const { data } = await api.post('/auth/login', { phone: form.phone })

      const token = data.token
      const user = data.user
      setAuthToken(token)
      localStorage.setItem('dream_user', JSON.stringify(user))

      // Миграция гостевого диалога в аккаунт (если есть)
      try {
        const raw = localStorage.getItem('dream_guest_messages')
        if (raw) {
          const msgs = JSON.parse(raw)
          if (Array.isArray(msgs) && msgs.length > 0) {
            const turns = []
            let pendingUser = null
            for (const m of msgs) {
              if (m?.role === 'user') {
                pendingUser = m.text || ''
              } else if (m?.role === 'bot') {
                const botText = m.text || ''
                if (pendingUser || botText) {
                  turns.push({ user: pendingUser || '', bot: botText })
                }
                pendingUser = null
              }
            }
            if (pendingUser) {
              turns.push({ user: pendingUser, bot: '' })
            }
            const profile = {
              name: localStorage.getItem('dream_name') || null,
              birth_date: localStorage.getItem('dream_birth_date') || null
            }
            if (turns.length > 0) {
              await api.post('/sessions/migrate', { turns, profile })
            }
          }
        }
      } catch (e) {
        console.warn('Не удалось мигрировать гостевой диалог:', e)
      }

      // Очистка гостевого состояния после миграции
      localStorage.removeItem('dream_guest_messages')
      localStorage.removeItem('dream_guest_stage')
      localStorage.removeItem('dream_guest_hint')
      localStorage.removeItem('dream_guest_session_id')

      navigate('/', { replace: true })
    } catch (err) {
      console.error('Ошибка входа:', err)
      const errorDetail = err.response?.data?.detail || ''
      if (errorDetail.includes('не найден') || err.response?.status === 404) {
        setError('Пользователь не найден. Зарегистрируйтесь, чтобы создать аккаунт.')
        setMode('register')
      } else {
        setError(errorDetail || 'Не удалось войти. Проверьте данные и попробуйте ещё раз.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (form) => {
    try {
      setLoading(true)
      setError(null)
      const { data } = await api.post('/auth/register', {
        phone: form.phone,
        name: form.name,
        birth_date: form.birth_date
      })

      const token = data.token
      const user = data.user
      setAuthToken(token)
      localStorage.setItem('dream_user', JSON.stringify(user))

      // Миграция гостевого диалога в аккаунт (если есть)
      try {
        const raw = localStorage.getItem('dream_guest_messages')
        if (raw) {
          const msgs = JSON.parse(raw)
          if (Array.isArray(msgs) && msgs.length > 0) {
            const turns = []
            let pendingUser = null
            for (const m of msgs) {
              if (m?.role === 'user') {
                pendingUser = m.text || ''
              } else if (m?.role === 'bot') {
                const botText = m.text || ''
                if (pendingUser || botText) {
                  turns.push({ user: pendingUser || '', bot: botText })
                }
                pendingUser = null
              }
            }
            if (pendingUser) {
              turns.push({ user: pendingUser, bot: '' })
            }
            const profile = {
              name: form.name || localStorage.getItem('dream_name') || null,
              birth_date: form.birth_date || localStorage.getItem('dream_birth_date') || null
            }
            if (turns.length > 0) {
              await api.post('/sessions/migrate', { turns, profile })
            }
          }
        }
      } catch (e) {
        console.warn('Не удалось мигрировать гостевой диалог:', e)
      }

      // Очистка гостевого состояния после миграции
      localStorage.removeItem('dream_guest_messages')
      localStorage.removeItem('dream_guest_stage')
      localStorage.removeItem('dream_guest_hint')
      localStorage.removeItem('dream_guest_session_id')

      navigate('/', { replace: true })
    } catch (err) {
      console.error('Ошибка регистрации:', err)
      const errorDetail = err.response?.data?.detail || ''
      if (errorDetail.includes('уже зарегистрирован')) {
        setError('Пользователь с таким номером уже зарегистрирован. Войдите в аккаунт.')
        setMode('login')
      } else {
        setError(errorDetail || 'Не удалось зарегистрироваться. Проверьте данные и попробуйте ещё раз.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="relative z-10 flex flex-col min-h-screen pt-10 pb-16">
      <div className="max-w-5xl mx-auto w-full px-4 space-y-8">
        <div className="flex items-center justify-between text-sm text-slate-400">
          <Link to="/" className="inline-flex items-center gap-2 hover:text-white transition-colors">
            <span aria-hidden="true">←</span>
            На главную
          </Link>
          <span className="tracking-[0.4em] uppercase text-xs text-slate-500">ИИ Сонник</span>
        </div>

        <div className="grid gap-8 md:grid-cols-[1.15fr_0.85fr] items-start">
          <div className="bg-slate-900/60 rounded-3xl border border-slate-800 p-8 space-y-6 shadow-xl card-glow relative overflow-hidden">
            <div className="pointer-events-none absolute -top-14 -right-10 h-48 w-48 rounded-full blur-2xl opacity-30"
                 style={{background: 'radial-gradient(closest-side, rgba(99,102,241,0.35), transparent)'}} />
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500 mb-3">
                {mode === 'login' ? 'Вход в аккаунт' : 'Регистрация'}
              </p>
              <h1 className="text-3xl font-semibold text-white mb-3">
                {mode === 'login' 
                  ? 'Войди в свой кабинет' 
                  : 'Создай связь с проводником снов'}
              </h1>
              <p className="text-slate-400 text-base">
                {mode === 'login' 
                  ? 'Введи номер телефона, чтобы войти в свой аккаунт и получить доступ к истории интерпретаций.'
                  : 'Для регистрации нужно указать имя, дату рождения и номер телефона. Это поможет персонализировать интерпретацию снов.'}
              </p>
            </div>

            <div className="grid gap-4">
              {BENEFITS.map((benefit) => (
                <div
                  key={benefit.title}
                  className="bg-slate-950/60 border border-slate-800 rounded-2xl p-4"
                >
                  <p className="text-sm uppercase tracking-[0.2em] text-purple-300/80 mb-2">{benefit.title}</p>
                  <p className="text-slate-300 text-sm">{benefit.text}</p>
                </div>
              ))}
            </div>

            {mode === 'login' ? (
              <div className="bg-gradient-to-r from-purple-600/30 to-indigo-600/30 border border-purple-500/30 rounded-2xl p-4 space-y-2">
                <p className="text-white font-semibold">Нет аккаунта?</p>
                <p className="text-sm text-white/80 mb-3">
                  Зарегистрируйся, чтобы сохранять историю интерпретаций и получать персональные подсказки.
                </p>
                <button
                  onClick={() => {
                    setMode('register')
                    setError(null)
                  }}
                  className="w-full bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg font-medium transition"
                >
                  Зарегистрироваться
                </button>
              </div>
            ) : (
              <div className="bg-gradient-to-r from-indigo-600/30 to-purple-600/30 border border-indigo-500/30 rounded-2xl p-4 space-y-2">
                <p className="text-white font-semibold">Уже есть аккаунт?</p>
                <p className="text-sm text-white/80 mb-3">
                  Войди в свой аккаунт, чтобы продолжить работу с сохранённой историей.
                </p>
                <button
                  onClick={() => {
                    setMode('login')
                    setError(null)
                  }}
                  className="w-full bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg font-medium transition"
                >
                  Войти
                </button>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {error && (
              <div className="bg-red-500/10 border border-red-500/40 text-red-200 px-4 py-2 rounded-xl text-sm">
                {error}
              </div>
            )}
            <AuthForm 
              mode={mode}
              onSuccess={mode === 'login' ? handleLogin : handleRegister} 
              isLoading={loading} 
              className="shadow-2xl" 
            />
          </div>
        </div>
      </div>
    </section>
  )
}