import React, { useRef, useMemo, useEffect, useState } from 'react'

function DialogProgress({ currentStage }) {
  const stages = ['greeting', 'exploration', 'analysis', 'closing']
  const stageNames = {
    greeting: 'Приветствие',
    exploration: 'Исследование',
    analysis: 'Анализ',
    closing: 'Завершение'
  }
  
  const currentIndex = stages.indexOf(currentStage)
  
  return (
    <div className="mb-4 pb-4 border-b border-slate-800">
      <div className="flex gap-2 mb-2">
        {stages.map((stage, idx) => (
          <div key={stage} className="flex-1">
            <div className={`h-2 rounded-full transition-all ${
              idx < currentIndex ? 'bg-purple-400' :
              idx === currentIndex ? 'bg-purple-500' : 
              'bg-slate-700'
            }`} />
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-400 text-center">
        {stageNames[currentStage] || 'Начало'}
      </p>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl px-4 py-3">
        <div className="flex gap-1">
          <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0ms'}} />
          <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '150ms'}} />
          <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '300ms'}} />
        </div>
      </div>
    </div>
  )
}

export default function ChatWindow({
  messages,
  onSend,
  disabled,
  onUploadAudio,
  onPlayVoice,
  onStopVoice,
  playingMessageId,
  voiceLoadingId,
  currentStage,
  hint
}) {
  const inputRef = useRef()
  const bottomRef = useRef(null)
  const [parallax, setParallax] = useState({ x: 0, y: 0 })

  const handleSubmit = (e) => {
    e.preventDefault()
    const text = inputRef.current.value.trim()
    if (!text) return
    onSend(text)
    inputRef.current.value = ''
  }

  // Автоскролл к последнему сообщению
  useEffect(() => {
    if (bottomRef.current?.scrollIntoView) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages.length])

  const currentStageValue = useMemo(() => {
    if (currentStage) return currentStage
    // Определяем этап из последнего сообщения бота
    const lastBotMsg = [...messages].reverse().find(m => m.role === 'bot')
    if (lastBotMsg && lastBotMsg.meta) {
      const meta = lastBotMsg.meta.toLowerCase()
      if (meta.includes('greeting')) return 'greeting'
      if (meta.includes('exploration')) return 'exploration'
      if (meta.includes('analysis')) return 'analysis'
      if (meta.includes('closing')) return 'closing'
    }
    return messages.length === 0 ? 'greeting' : 'exploration'
  }, [messages, currentStage])

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const relX = (e.clientX - rect.left) / rect.width - 0.5
    const relY = (e.clientY - rect.top) / rect.height - 0.5
    setParallax({ x: relX, y: relY })
  }
  const handleMouseLeave = () => setParallax({ x: 0, y: 0 })

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div
      className="relative flex flex-col h-full bg-slate-900/40 rounded-3xl border border-slate-800 p-6 overflow-hidden"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="sky-decor">
        <div className="stars" style={{ transform: `translate(${parallax.x * -4}px, ${parallax.y * -4}px)` }} />
        <div className="moon" style={{ transform: `translate(${parallax.x * -8}px, ${parallax.y * -6}px)` }} />
        <div className="cloud cloud-1" style={{ transform: `translate(${parallax.x * 12}%, ${parallax.y * 3}%)` }} />
        <div className="cloud cloud-2" style={{ transform: `translate(${parallax.x * 8}%, ${parallax.y * 2}%)` }} />
        <div className="cloud cloud-3" style={{ transform: `translate(${parallax.x * 16}%, ${parallax.y * 4}%)` }} />
      </div>
      {messages.length > 0 && <DialogProgress currentStage={currentStageValue} />}
      
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg, idx) => {
          const isBot = msg.role === 'bot'
          const isPlaying = playingMessageId === msg.id
          const isLoading = voiceLoadingId === msg.id

          return (
            <div key={msg.id || idx} className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
              <div
                className={`rounded-2xl px-4 py-3 max-w-[80%] ${
                  isBot
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                    : 'bg-slate-800 text-slate-100'
                }`}
              >
                <p className="text-sm text-slate-300 mb-1">{msg.meta}</p>
                <p>{msg.text}</p>
                {isBot && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-white/80">
                    <button
                      type="button"
                      onClick={() =>
                        isPlaying
                          ? onStopVoice && onStopVoice()
                          : onPlayVoice && onPlayVoice(msg)
                      }
                      disabled={disabled || isLoading}
                      className={`inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/30 transition ${
                        isPlaying ? 'bg-white text-slate-900' : 'bg-white/10 hover:bg-white/20'
                      }`}
                      aria-label={
                        isPlaying
                          ? 'Остановить озвучку'
                          : isLoading
                            ? 'Озвучка загружается'
                            : 'Озвучить ответ'
                      }
                    >
                      {isLoading ? '…' : isPlaying ? '■' : '▶'}
                    </button>
                    <span className="text-white/70">
                      {isLoading ? 'Подготовка аудио...' : isPlaying ? 'Идет озвучка' : 'Озвучить ответ'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
        {disabled && <TypingIndicator />}
        {messages.length === 0 && (
          <p className="text-center text-slate-500">Поделись сном — я подскажу, что он может значить.</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[220px]">
            <textarea
              ref={inputRef}
              rows={3}
              onKeyDown={handleKeyDown}
              className="w-full rounded-2xl bg-slate-950/70 border border-slate-800 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              placeholder="«Мне приснился океан...»"
              disabled={disabled}
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={disabled}
              className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-r from-purple-500 via-indigo-500 to-blue-500 text-2xl text-white disabled:opacity-40 transition hover:shadow-lg"
              aria-label="Отправить текст"
            >
              {disabled ? '…' : '📤'}
            </button>
            <label
              className={`flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-700 bg-slate-900/70 text-xl cursor-pointer transition hover:border-purple-400 ${
                disabled ? 'opacity-40 pointer-events-none' : ''
              }`}
              aria-label="Отправить голосовое сообщение"
            >
              🎙️
              <input type="file" accept="audio/*" hidden onChange={onUploadAudio} disabled={disabled} />
            </label>
          </div>
        </div>
      </form>
    </div>
  )
}