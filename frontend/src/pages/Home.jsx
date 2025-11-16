import React, { useEffect, useRef, useState } from 'react'
import ChatWindow from '../components/ChatWindow'
import { api, setAuthToken } from '../services/api'
import { useNavigate } from 'react-router-dom'

const GUEST_MESSAGES_KEY = 'dream_guest_messages'
const GUEST_STAGE_KEY = 'dream_guest_stage'
const GUEST_HINT_KEY = 'dream_guest_hint'
const GUEST_DEFAULT_NAME = 'Гость'
const createGuestSessionId = () => `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
const withMessageId = (message) => {
  if (!message) return null
  return message.id ? message : { ...message, id: generateMessageId() }
}
const applyMessageIds = (items = []) => items.map((msg) => withMessageId(msg)).filter(Boolean)

// Компонент для гостевой формы (имя и дата рождения)
function GuestProfileForm({ onSubmit, onSkip, className = '' }) {
  const [form, setForm] = useState({
    name: '',
    birth_date: ''
  })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    // Загружаем сохраненные данные из localStorage
    const savedName = localStorage.getItem('dream_name')
    const savedBirthDate = localStorage.getItem('dream_birth_date')
    
    if (savedName || savedBirthDate) {
      setForm({
        name: savedName || '',
        birth_date: savedBirthDate || ''
      })
    }
  }, [])

  const validate = () => {
    const newErrors = {}
    
    if (form.birth_date) {
      const birthDate = new Date(form.birth_date)
      const today = new Date()
      const age = today.getFullYear() - birthDate.getFullYear()
      
      if (birthDate > today) {
        newErrors.birth_date = 'Дата рождения не может быть в будущем'
      } else if (age > 120) {
        newErrors.birth_date = 'Проверьте дату рождения'
      }
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm({ ...form, [name]: value })
    
    // Сохраняем в localStorage
    if (name === 'name') {
      localStorage.setItem('dream_name', value)
    } else if (name === 'birth_date') {
      localStorage.setItem('dream_birth_date', value)
    }
    
    // Очищаем ошибку при изменении
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' })
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSubmit(form)
    }
  }

  return (
    <div className={`bg-slate-900/70 rounded-2xl p-6 space-y-4 shadow-xl border border-slate-800 w-full ${className}`}>
      <div className="text-center mb-4">
        <h2 className="text-2xl font-semibold text-white mb-2">Попробуй без регистрации</h2>
        <p className="text-sm text-slate-400">Укажи имя и дату рождения для персонализированного общения</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-300 mb-1">
            Имя (необязательно)
          </label>
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Как к тебе обращаться?"
            className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-300 mb-1">
            Дата рождения (необязательно)
          </label>
          <input
            type="date"
            name="birth_date"
            value={form.birth_date}
            onChange={handleChange}
            max={new Date().toISOString().split('T')[0]}
            className={`w-full rounded-lg bg-slate-800 border px-3 py-2 focus:outline-none focus:ring-2 transition-colors ${
              errors.birth_date
                ? 'border-red-500 focus:ring-red-500'
                : 'border-slate-700 focus:ring-purple-500'
            }`}
          />
          {errors.birth_date && (
            <p className="text-red-400 text-xs mt-1">{errors.birth_date}</p>
          )}
          <p className="text-xs text-slate-500 mt-1">Используется для более точной интерпретации</p>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-500 py-2 rounded-lg font-medium hover:opacity-90 transition text-white"
          >
            Начать общение
          </button>
          <button
            type="button"
            onClick={onSkip}
            className="px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors underline text-sm"
          >
            Пропустить
          </button>
        </div>
      </form>
    </div>
  )
}

// Компонент для предложения регистрации
function RegistrationPrompt({ onRegister, onDismiss }) {
  return (
    <div className="bg-gradient-to-r from-purple-600/20 to-indigo-600/20 border border-purple-500/40 rounded-2xl p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-2">💾 Сохрани свою историю</h3>
          <p className="text-slate-300 text-sm mb-4">
            Чтобы сохранить историю интерпретаций и получить персональные insights, 
            введи данные для регистрации. Это займет всего минуту!
          </p>
          <div className="flex gap-3">
            <button
              onClick={onRegister}
              className="bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-6 py-2 rounded-lg font-medium hover:opacity-90 transition"
            >
              Зарегистрироваться
            </button>
            <button
              onClick={onDismiss}
              className="px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors underline text-sm"
            >
              Позже
            </button>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-slate-400 hover:text-slate-200 transition-colors ml-4"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

const STAGE_LABELS = {
  greeting: 'Приветствие',
  exploration: 'Исследование деталей',
  analysis: 'Анализ образов',
  closing: 'Завершение и рекомендации'
}

const STAGE_DESCRIPTIONS = {
  greeting: 'Делимся контекстом, чтобы ИИ уловил настроение и тему сна.',
  exploration: 'Уточняем сюжет и эмоции, собираем детали для интерпретации.',
  analysis: 'ИИ сопоставляет символы и опыт, чтобы подсказать возможные смыслы.',
  closing: 'Получаем вывод и практические шаги для осознанного пробуждения.'
}

function ExperienceHighlights({ currentStage, hint, isGuest, messageCount, onRequestAuth }) {
  const stageLabel = STAGE_LABELS[currentStage] || 'Старт диалога'
  const stageDescription =
    STAGE_DESCRIPTIONS[currentStage] ||
    'Расскажи первый сон и получи индивидуальную интерпретацию за минуту.'

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Текущий этап</p>
        <p className="text-lg font-semibold text-white mb-1">{stageLabel}</p>
        <p className="text-sm text-slate-400">{stageDescription}</p>
      </div>

      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">Умная подсказка</p>
        <p className={`text-sm ${hint ? 'text-slate-200' : 'text-slate-500'}`}>
          {hint || 'Подсказка появится после первого ответа ИИ.'}
        </p>
      </div>

      <div className="bg-gradient-to-br from-purple-600/40 via-indigo-600/30 to-slate-900 rounded-2xl border border-purple-500/30 p-4">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60 mb-2">Режим</p>
        <p className="text-lg font-semibold text-white">
          {isGuest ? 'Гостевой доступ' : 'Личный кабинет'}
        </p>
        <p className="text-sm text-white/80 mt-1">
          {isGuest
            ? 'Сохрани прогресс, чтобы не потерять интерпретации.'
            : 'История снов синхронизирована и доступна с любого устройства.'}
        </p>
        {isGuest && (
          <button
            onClick={onRequestAuth}
            className="mt-3 inline-flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium px-4 py-2 rounded-xl transition"
          >
            <span>Сохранить прогресс</span>
            <span aria-hidden>→</span>
          </button>
        )}
        <p className="text-xs text-white/60 mt-4">{messageCount || 0} сообщений в текущей сессии</p>
      </div>
    </div>
  )
}

function MobileInsightCard({ currentStage, hint, isGuest, onRequestAuth }) {
  const stageLabel = STAGE_LABELS[currentStage] || 'Старт диалога'
  return (
    <div className="lg:hidden bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-500 mb-1">Сейчас</p>
        <p className="text-lg font-semibold text-white">{stageLabel}</p>
      </div>
      <p className="text-sm text-slate-300 flex items-start gap-2">
        <span className="text-purple-400">💡</span>
        {hint || 'Подсказка появится после первого ответа ИИ.'}
      </p>
      {isGuest && (
        <button
          onClick={onRequestAuth}
          className="self-start bg-white/10 hover:bg-white/20 text-white text-sm font-medium px-4 py-2 rounded-xl transition"
        >
          Сохранить прогресс
        </button>
      )}
    </div>
  )
}

function ProfileSidebar({
  open,
  onClose,
  user,
  guestProfile,
  isGuest,
  onSupport,
  onClearChat,
  canClear,
  onLogout,
  onLogin,
  loading
}) {
  const displayName = user?.name || guestProfile?.name || GUEST_DEFAULT_NAME
  const displayBirth = user?.birth_date || guestProfile?.birth_date || '—'
  const displayMode = isGuest ? 'Гостевой режим' : 'Личный кабинет'

  return (
    <>
      <div
        className={`fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />
      <aside
        className={`fixed top-0 right-0 h-full w-full max-w-sm bg-slate-950 border-l border-slate-800 shadow-2xl transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col p-6 gap-6">
          <div className="flex items-center justify-between">
            <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Профиль</p>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white transition"
              aria-label="Закрыть панель"
            >
              ✕
            </button>
          </div>

          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-2xl">
              👤
            </div>
            <div>
              <p className="text-lg text-white font-semibold">{displayName}</p>
              <p className="text-sm text-slate-400">{displayMode}</p>
            </div>
          </div>

          <div className="space-y-3 text-sm text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-500">Дата рождения</span>
              <span>{displayBirth}</span>
            </div>
            {!isGuest && (
              <div className="flex justify-between">
                <span className="text-slate-500">Телефон</span>
                <span>{user?.phone || '—'}</span>
              </div>
            )}
          </div>

          <div className="mt-auto space-y-3">
            <button
              onClick={onSupport}
              className="w-full rounded-2xl bg-gradient-to-r from-emerald-400 to-teal-400 px-4 py-3 text-emerald-950 font-semibold hover:brightness-110 transition"
            >
              💚 Поддержать проект
            </button>
            <button
              onClick={onClearChat}
              disabled={!canClear || loading}
              className="w-full rounded-2xl border border-slate-700 px-4 py-3 text-slate-200 hover:border-slate-500 transition disabled:opacity-40 disabled:pointer-events-none"
            >
              🧹 Очистить диалог
            </button>
            {isGuest ? (
              <button
                onClick={onLogin}
                className="w-full rounded-2xl border border-purple-500 px-4 py-3 text-purple-200 hover:bg-purple-500/10 transition"
              >
                Войти / Зарегистрироваться
              </button>
            ) : (
              <button
                onClick={onLogout}
                className="w-full rounded-2xl border border-slate-700 px-4 py-3 text-slate-300 hover:border-red-500 hover:text-red-400 transition"
              >
                Выйти
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

function ChatPreview({ onStartGuest, onShowAuth }) {
  const previewMessages = [
    { role: 'user', meta: 'Ты', text: 'Мне приснился океан и я не мог добраться до берега.' },
    {
      role: 'bot',
      meta: 'ИИ Сонник · Анализ',
      text: 'Океан часто отражает эмоции. Чувство беспомощности может намекать на усталость или страх перемен.'
    }
  ]

  return (
    <div className="flex flex-col h-full bg-slate-900/40 rounded-3xl border border-slate-800 p-6">
      <div className="flex-1 space-y-4">
        <div className="text-sm text-slate-400">Посмотри, как выглядит диалог</div>
        <div className="space-y-3">
          {previewMessages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'bot' ? 'justify-start' : 'justify-end'}`}>
              <div
                className={`rounded-2xl px-4 py-3 max-w-[80%] ${
                  msg.role === 'bot'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                    : 'bg-slate-800 text-slate-100'
                }`}
              >
                <p className="text-xs text-slate-300 mb-1">{msg.meta}</p>
                <p className="text-sm">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 bg-slate-950/60 border border-slate-800 rounded-2xl p-4">
        <p className="text-base font-semibold text-white mb-1">Готов начать?</p>
        <p className="text-sm text-slate-400 mb-4">
          Поделись сном в гостевом режиме или войди, чтобы сохранять историю.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={onStartGuest}
            className="flex-1 min-w-[140px] bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-4 py-2 rounded-xl font-medium hover:opacity-90 transition"
          >
            Попробовать
          </button>
          <button
            onClick={onShowAuth}
            className="flex-1 min-w-[140px] bg-slate-800 border border-slate-700 text-slate-100 px-4 py-2 rounded-xl font-medium hover:bg-slate-700 transition"
          >
            Войти
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [messages, setMessages] = useState([])
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [currentStage, setCurrentStage] = useState(null)
  const [hint, setHint] = useState(null)
  const [isGuest, setIsGuest] = useState(false)
  const [guestSessionId, setGuestSessionId] = useState(null)
  const [guestProfile, setGuestProfile] = useState(null)
  const [showGuestForm, setShowGuestForm] = useState(false)
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [playingMessageId, setPlayingMessageId] = useState(null)
  const [voiceLoadingId, setVoiceLoadingId] = useState(null)
  const audioRef = useRef(null)
  const stopVoicePlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    setPlayingMessageId(null)
    setVoiceLoadingId(null)
  }

  const resetGuestSession = () => {
    const newId = createGuestSessionId()
    localStorage.setItem('dream_guest_session_id', newId)
    setGuestSessionId(newId)
  }

  const clearGuestStorage = () => {
    localStorage.removeItem(GUEST_MESSAGES_KEY)
    localStorage.removeItem(GUEST_STAGE_KEY)
    localStorage.removeItem(GUEST_HINT_KEY)
  }

  const resetConversationState = () => {
    stopVoicePlayback()
    setMessages([])
    setCurrentStage(null)
    setHint(null)
    setShowRegistrationPrompt(false)
  }

  const restoreGuestConversation = () => {
    try {
      const storedMessages = localStorage.getItem(GUEST_MESSAGES_KEY)
      if (storedMessages) {
        const parsed = JSON.parse(storedMessages)
        if (Array.isArray(parsed)) {
          setMessages(applyMessageIds(parsed))
        }
      }
    } catch (err) {
      console.error('Не удалось восстановить гостевой диалог:', err)
      localStorage.removeItem(GUEST_MESSAGES_KEY)
    }

    const storedStage = localStorage.getItem(GUEST_STAGE_KEY)
    if (storedStage) {
      setCurrentStage(storedStage)
    }

    const storedHint = localStorage.getItem(GUEST_HINT_KEY)
    if (storedHint) {
      setHint(storedHint)
    }
  }

  useEffect(() => {
    return () => stopVoicePlayback()
  }, [])

  // Генерируем или загружаем guest_session_id
  useEffect(() => {
    let sessionId = localStorage.getItem('dream_guest_session_id')
    if (!sessionId) {
      sessionId = createGuestSessionId()
      localStorage.setItem('dream_guest_session_id', sessionId)
    }
    setGuestSessionId(sessionId)

    // Проверяем, есть ли сохраненный профиль гостя
    const savedName = localStorage.getItem('dream_name')
    const savedBirthDate = localStorage.getItem('dream_birth_date')
    if (savedName || savedBirthDate) {
      setGuestProfile({
        name: savedName || null,
        birth_date: savedBirthDate || null
      })
    }

    // Проверяем, есть ли токен авторизации
    const cached = localStorage.getItem('dream_token')
    const cachedUser = localStorage.getItem('dream_user')
    if (cached && cachedUser) {
      setToken(cached)
      setUser(JSON.parse(cachedUser))
      setAuthToken(cached)
      setIsGuest(false)
      fetchSessions()
    } else {
      // Если нет авторизации, показываем чат в гостевом режиме
      setIsGuest(true)
      restoreGuestConversation()
    }
  }, [])

  useEffect(() => {
    if (!isGuest) return

    if (messages.length > 0) {
      localStorage.setItem(GUEST_MESSAGES_KEY, JSON.stringify(messages))
    } else {
      localStorage.removeItem(GUEST_MESSAGES_KEY)
    }

    if (currentStage) {
      localStorage.setItem(GUEST_STAGE_KEY, currentStage)
    } else {
      localStorage.removeItem(GUEST_STAGE_KEY)
    }

    if (hint) {
      localStorage.setItem(GUEST_HINT_KEY, hint)
    } else {
      localStorage.removeItem(GUEST_HINT_KEY)
    }
  }, [messages, isGuest, currentStage, hint])

  const fetchSessions = async () => {
    if (isGuest) return // Для гостей не загружаем сессии
    
    try {
      const { data } = await api.get('/sessions')
      setSessions(data || [])
      const mapped = data
        .slice()
        .reverse()
        .flatMap((session) => [
          { role: 'user', text: session.message, meta: 'Ты' },
          { role: 'bot', text: session.response, meta: `ИИ Сонник · ${session.mood}` }
        ])
      setMessages(applyMessageIds(mapped))
      
      // Устанавливаем текущий этап из последней сессии
      if (data.length > 0) {
        const lastSession = data[0]
        setCurrentStage(lastSession.mood || 'greeting')
      }
    } catch (err) {
      console.error('Ошибка загрузки сессий:', err)
      // Если ошибка 401, переключаемся на гостевой режим
      if (err.response?.status === 401) {
        setToken(null)
        setUser(null)
        setIsGuest(true)
        setMessages([])
        setCurrentStage(null)
        setHint(null)
        setError('Сессия истекла. Продолжаем в гостевом режиме.')
      }
    }
  }

  const handleGuestProfileSubmit = (profile) => {
    setGuestProfile({
      name: profile.name || null,
      birth_date: profile.birth_date || null
    })
    setShowGuestForm(false)
    // Сохраняем в localStorage
    if (profile.name) {
      localStorage.setItem('dream_name', profile.name)
    }
    if (profile.birth_date) {
      localStorage.setItem('dream_birth_date', profile.birth_date)
    }
  }

  const handleGuestSkip = () => {
    setShowGuestForm(false)
    setGuestProfile({ name: null, birth_date: null })
  }

  const handleSend = async (text) => {
    setError(null)
    setLoading(true)
    const userMessage = withMessageId({ role: 'user', text, meta: 'Ты' })
    setMessages((prev) => [...prev, userMessage])
    try {
      const payload = {
        message: text
      }
      
      if (isGuest) {
        payload.guest_session_id = guestSessionId
        payload.guest_profile = {
          name: GUEST_DEFAULT_NAME,
          birth_date: guestProfile?.birth_date || null
        }
      }
      
      const { data } = await api.post('/chat', payload)
      const botMessage = withMessageId({ role: 'bot', text: data.reply, meta: `ИИ Сонник · ${data.stage}` })
      setMessages((prev) => [...prev, botMessage])
      setCurrentStage(data.stage)
      setHint(data.hint)
      
      // Показываем предложение регистрации после первой интерпретации
      if (isGuest && data.suggest_registration && !showRegistrationPrompt) {
        setShowRegistrationPrompt(true)
      }
    } catch (err) {
      console.error('Ошибка отправки сообщения:', err)
      if (err.response?.status === 401 && !isGuest) {
        setError('Сессия истекла. Продолжаем в гостевом режиме.')
        setIsGuest(true)
        setToken(null)
        setUser(null)
      } else {
        setError(err.response?.data?.detail || 'Сервис временно недоступен.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleAudioUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    const base64 = await fileToBase64(file)
    const { data } = await api.post('/asr', { audio_base64: base64 })
    handleSend(data.text)
    event.target.value = ''
  }

  const handlePlayVoice = async (message) => {
    if (!message?.text) return

    if (playingMessageId === message.id) {
      stopVoicePlayback()
      return
    }

    setVoiceLoadingId(message.id)

    try {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
        audioRef.current = null
        setPlayingMessageId(null)
      }
      const { data } = await api.post('/tts', { text: message.text })
      const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`)
      audioRef.current = audio
      audio.onended = () => stopVoicePlayback()
      setPlayingMessageId(message.id)
      setVoiceLoadingId(null)
      await audio.play()
    } catch (err) {
      console.error('Ошибка озвучки:', err)
      setError('Не удалось озвучить ответ. Попробуйте позже.')
      stopVoicePlayback()
    }
  }

  const handleStopVoice = () => {
    stopVoicePlayback()
  }

  const handlePay = async () => {
    if (isGuest) {
      setError('Для поддержки проекта необходимо войти в систему.')
      navigate('/auth')
      return
    }
    try {
      const defaultAmount = 199
      const { data } = await api.post('/payments', {
        amount: Number(defaultAmount),
        description: 'Поддержка проекта'
      })
      const chatUrl = `${window.location.origin}/`
      const url = `${data.payment_url}?chat_url=${encodeURIComponent(chatUrl)}`
      window.open(url, '_blank', 'noopener')
    } catch (err) {
      console.error('Ошибка создания платежа:', err)
      setError(err.response?.data?.detail || 'Не удалось создать платеж. Попробуйте позже.')
    }
  }

  const handleClearChat = async () => {
    if (messages.length === 0 && !hint && !showRegistrationPrompt) return
    const confirmed = window.confirm('Очистить текущий диалог? История будет потеряна.')
    if (!confirmed) return

    setError(null)

    if (isGuest) {
      resetConversationState()
      clearGuestStorage()
      resetGuestSession()
      return
    }

    try {
      setLoading(true)
      await api.delete('/sessions')
      resetConversationState()
      clearGuestStorage()
      await fetchSessions()
    } catch (err) {
      console.error('Не удалось очистить историю:', err)
      setError('Не удалось очистить историю. Попробуйте позже.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    // Очищаем токен и данные пользователя
    localStorage.removeItem('dream_token')
    localStorage.removeItem('dream_user')
    localStorage.removeItem('dream_name')
    localStorage.removeItem('dream_birth_date')
    clearGuestStorage()
    setToken(null)
    setUser(null)
    setIsGuest(true)
    resetConversationState()
    setError(null)
    setAuthToken(null)
    setGuestProfile({ name: null, birth_date: null })
    resetGuestSession()
  }

  const openGuestPanel = () => {
    setShowGuestForm(true)
  }

  const goToAuthPage = () => {
    setShowGuestForm(false)
    navigate('/auth')
  }

  const handleStartGuest = () => {
    openGuestPanel()
  }

  const handleRegisterFromPrompt = () => {
    setShowRegistrationPrompt(false)
    goToAuthPage()
  }

  // Определяем, что показывать
  const showChat = token || isGuest
  const showWelcome = !showChat && !showGuestForm
  const canClearConversation = messages.length > 0 || !!hint || showRegistrationPrompt

  return (
    <>
    <section className="max-w-6xl h-full mx-auto py-6 px-4 overflow-y-auto lg:overflow-hidden">
      <div className="flex flex-col gap-8 lg:grid lg:grid-cols-[1.15fr_0.85fr] lg:items-start lg:h-full lg:overflow-hidden">
        <div className="order-2 lg:order-1 space-y-6 lg:overflow-y-auto lg:pr-4">
          <header className="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/70 p-6 sm:p-8 card-glow">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/40 via-slate-950 to-slate-950 pointer-events-none" aria-hidden />
            <div className="relative z-10 text-center space-y-3">
              <p className="uppercase tracking-[0.25em] text-[0.7rem] text-slate-400">ИИ Сонник</p>
              <h1 className="text-3xl sm:text-4xl font-semibold text-white">Осознанные интерпретации снов</h1>
              <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
                Помогаем расшифровать эмоции и найти опору в реальности. Делись снами голосом или текстом — мы поддержим 24/7.
              </p>
              <div className="flex flex-wrap justify-center gap-2 sm:gap-3 pt-3 text-[0.65rem] sm:text-xs uppercase tracking-[0.2em]">
                <span className="px-3 py-1 rounded-full border border-white/10 text-white/80">ASR · TTS</span>
                <span className="px-3 py-1 rounded-full border border-white/10 text-white/80">Личный прогресс</span>
                <span className="px-3 py-1 rounded-full border border-white/10 text-white/80">Эмпатичный ИИ</span>
              </div>
            </div>
            {/* dreamy decorative orbs */}
            <div className="pointer-events-none absolute -top-16 -right-10 h-56 w-56 rounded-full blur-2xl opacity-40"
                 style={{background: 'radial-gradient(closest-side, rgba(99,102,241,0.35), transparent)'}} />
            <div className="pointer-events-none absolute -bottom-20 -left-10 h-64 w-64 rounded-full blur-2xl opacity-30"
                 style={{background: 'radial-gradient(closest-side, rgba(236,72,153,0.28), transparent)'}} />
            <div className="absolute top-6 right-6 z-20 flex items-center gap-3">
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="h-10 w-10 rounded-full border border-slate-700 bg-slate-900/80 text-xl text-slate-200 hover:border-purple-400 transition"
                aria-label="Открыть профиль"
              >
                👤
              </button>
            </div>
          </header>

          <MobileInsightCard
            currentStage={currentStage}
            hint={hint}
            isGuest={isGuest || !token}
            onRequestAuth={goToAuthPage}
          />

          <div className="hidden lg:block">
            <ExperienceHighlights
              currentStage={currentStage}
              hint={hint}
              isGuest={isGuest || !token}
              messageCount={messages.length}
              onRequestAuth={goToAuthPage}
            />
          </div>

          {/* История снов под вкладками */}
          {!isGuest && token && sessions.length > 0 && (
            <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-4 card-glow">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm uppercase tracking-[0.2em] text-slate-500">История снов</p>
                <button
                  onClick={fetchSessions}
                  className="text-xs px-3 py-1 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 transition"
                  disabled={loading}
                >
                  Обновить
                </button>
              </div>
              <ul className="divide-y divide-slate-800">
                {sessions.slice(0, 6).map((s, idx) => {
                  const date = s.created_at ? new Date(s.created_at) : null
                  const dateStr = date ? date.toLocaleString() : ''
                  const summary = (s.response || s.message || '').replace(/\s+/g, ' ').trim()
                  const short = summary.length > 140 ? summary.slice(0, 137) + '…' : summary
                  return (
                    <li key={idx} className="py-3 flex items-start gap-3">
                      <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white text-sm shrink-0">
                        {s.mood === 'closing' ? '☾' : '✦'}
                      </div>
                      <div className="min-w-0">
                        <p className="text-slate-200 text-sm">{short || 'Без текста'}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {dateStr} · этап: {s.mood || '—'}
                        </p>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/40 text-red-200 px-4 py-2 rounded-xl">
              {error}
            </div>
          )}

          {showRegistrationPrompt && (
            <RegistrationPrompt
              onRegister={handleRegisterFromPrompt}
              onDismiss={() => setShowRegistrationPrompt(false)}
            />
          )}

          {(isGuest || !token) && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4">
            <div className="flex flex-wrap items-start sm:items-center justify-between gap-3">
              <div>
                <p className="text-[0.65rem] uppercase tracking-[0.3em] text-slate-500">Как продолжить</p>
                <h3 className="text-lg sm:text-xl font-semibold text-white">Выбери режим общения</h3>
                <p className="text-sm text-slate-400">Можно начать как гость, а позже сохранить историю.</p>
              </div>
              <div className="flex flex-wrap gap-2 w-full sm:w-auto">
                <button
                  onClick={handleStartGuest}
                  className="flex-1 sm:flex-none bg-gradient-to-r from-purple-500 to-indigo-500 text-white px-4 py-2 rounded-xl font-medium hover:opacity-90 transition"
                >
                  Гостевой режим
                </button>
                <button
                  onClick={goToAuthPage}
                  className="flex-1 sm:flex-none px-4 py-2 rounded-xl border border-slate-700 text-slate-100 hover:bg-slate-800 transition"
                >
                  Войти
                </button>
              </div>
            </div>
            {showWelcome && (
              <ul className="grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">✦</span>
                  Получи первую интерпретацию бесплатно.
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">✦</span>
                  Гибко переключайся между текстом и голосом.
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">✦</span>
                  Сохраняй важные сны, когда будешь готов.
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">✦</span>
                  Получай подсказки на каждом этапе диалога.
                </li>
              </ul>
            )}
          </div>
          )}

          {showGuestForm && (
            <GuestProfileForm
              onSubmit={handleGuestProfileSubmit}
              onSkip={handleGuestSkip}
              className="shadow-2xl"
            />
          )}
        </div>

        <div className="order-1 lg:order-2 min-h-[60vh] lg:min-h-0 lg:h-full">
          <div className="h-full">
            {showChat ? (
              <ChatWindow
                messages={messages}
                disabled={loading}
                onSend={handleSend}
                onUploadAudio={handleAudioUpload}
                onPlayVoice={handlePlayVoice}
                onStopVoice={handleStopVoice}
                playingMessageId={playingMessageId}
                voiceLoadingId={voiceLoadingId}
                currentStage={currentStage}
                hint={hint}
              />
            ) : (
              <ChatPreview
                onStartGuest={handleStartGuest}
                onShowAuth={goToAuthPage}
              />
            )}
          </div>
        </div>
      </div>
    </section>
      <ProfileSidebar
        open={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        user={user}
        guestProfile={guestProfile}
        isGuest={isGuest || !token}
        onSupport={handlePay}
        onClearChat={handleClearChat}
        canClear={canClearConversation}
        onLogout={() => {
          handleLogout()
          setIsSidebarOpen(false)
        }}
        onLogin={() => {
          setIsSidebarOpen(false)
          goToAuthPage()
        }}
        loading={loading}
      />
    </>
  )
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}