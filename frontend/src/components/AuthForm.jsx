import React, { useState, useEffect } from 'react'

function formatPhone(value) {
  // Удаляем все нецифровые символы кроме +
  const cleaned = value.replace(/[^\d+]/g, '')
  
  // Если начинается не с +, добавляем +7
  if (!cleaned.startsWith('+')) {
    if (cleaned.startsWith('7') || cleaned.startsWith('8')) {
      return '+' + cleaned.replace(/^[78]/, '7')
    }
    return '+7' + cleaned
  }
  
  // Ограничиваем длину
  if (cleaned.length > 12) {
    return cleaned.slice(0, 12)
  }
  
  return cleaned
}

export default function AuthForm({ mode = 'login', onSuccess, isLoading, className = '' }) {
  const [form, setForm] = useState({
    phone: '',
    name: '',
    birth_date: ''
  })
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})

  // Загружаем сохраненные данные из localStorage
  useEffect(() => {
    const savedPhone = localStorage.getItem('dream_phone')
    const savedName = localStorage.getItem('dream_name')
    const savedBirthDate = localStorage.getItem('dream_birth_date')
    
    if (savedPhone || savedName || savedBirthDate) {
      setForm({
        phone: savedPhone || '',
        name: savedName || '',
        birth_date: savedBirthDate || ''
      })
    }
  }, [])

  const validate = () => {
    const newErrors = {}
    
    // Валидация телефона
    if (!form.phone) {
      newErrors.phone = 'Номер телефона обязателен'
    } else if (!/^\+7\d{10}$/.test(form.phone.replace(/\s/g, ''))) {
      newErrors.phone = 'Введите корректный номер телефона (+7XXXXXXXXXX)'
    }
    
    // Для регистрации все поля обязательны
    if (mode === 'register') {
      if (!form.name || form.name.trim().length === 0) {
        newErrors.name = 'Имя обязательно для регистрации'
      }
      
      if (!form.birth_date) {
        newErrors.birth_date = 'Дата рождения обязательна для регистрации'
      } else {
        const birthDate = new Date(form.birth_date)
        const today = new Date()
        const age = today.getFullYear() - birthDate.getFullYear()
        
        if (birthDate > today) {
          newErrors.birth_date = 'Дата рождения не может быть в будущем'
        } else if (age > 120) {
          newErrors.birth_date = 'Проверьте дату рождения'
        }
      }
    } else {
      // Для авторизации дата рождения необязательна, но валидируем если указана
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
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    let newValue = value
    
    // Форматирование телефона
    if (name === 'phone') {
      newValue = formatPhone(value)
    }
    
    setForm({ ...form, [name]: newValue })
    
    // Сохраняем в localStorage
    if (name === 'phone') {
      localStorage.setItem('dream_phone', newValue)
    } else if (name === 'name') {
      localStorage.setItem('dream_name', newValue)
    } else if (name === 'birth_date') {
      localStorage.setItem('dream_birth_date', newValue)
    }
    
    // Очищаем ошибку при изменении
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' })
    }
  }

  const handleBlur = (e) => {
    setTouched({ ...touched, [e.target.name]: true })
    validate()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setTouched({ phone: true, name: true, birth_date: true })
    
    if (validate()) {
      onSuccess(form)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={`bg-slate-900/70 rounded-2xl p-6 space-y-4 shadow-xl border border-slate-800 w-full ${className}`}
    >
      <div className="text-center mb-4">
        <h2 className="text-2xl font-semibold text-white mb-2">
          {mode === 'login' ? 'Вход в аккаунт' : 'Регистрация'}
        </h2>
        <p className="text-sm text-slate-400">
          {mode === 'login' 
            ? 'Введите номер телефона для входа' 
            : 'Заполните форму для создания аккаунта'}
        </p>
      </div>

      <div>
        <label className="block text-sm text-slate-300 mb-1">
          Номер телефона <span className="text-red-400">*</span>
        </label>
        <input
          name="phone"
          type="tel"
          required
          value={form.phone}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="+7 (999) 123-45-67"
          className={`w-full rounded-lg bg-slate-800 border px-3 py-2 focus:outline-none focus:ring-2 transition-colors ${
            errors.phone && touched.phone
              ? 'border-red-500 focus:ring-red-500'
              : 'border-slate-700 focus:ring-purple-500'
          }`}
        />
        {errors.phone && touched.phone && (
          <p className="text-red-400 text-xs mt-1">{errors.phone}</p>
        )}
        <p className="text-xs text-slate-500 mt-1">Нужен только для сохранения ваших снов</p>
      </div>

      {mode === 'register' && (
        <>
          <div>
            <label className="block text-sm text-slate-300 mb-1">
              Имя <span className="text-red-400">*</span>
            </label>
            <input
              name="name"
              required={mode === 'register'}
              value={form.name}
              onChange={handleChange}
              onBlur={handleBlur}
              placeholder="Как к вам обращаться?"
              className={`w-full rounded-lg bg-slate-800 border px-3 py-2 focus:outline-none focus:ring-2 transition-colors ${
                errors.name && touched.name
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-slate-700 focus:ring-purple-500'
              }`}
            />
            {errors.name && touched.name && (
              <p className="text-red-400 text-xs mt-1">{errors.name}</p>
            )}
            <p className="text-xs text-slate-500 mt-1">Помогает персонализировать общение</p>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">
              Дата рождения <span className="text-red-400">*</span>
            </label>
            <input
              type="date"
              name="birth_date"
              required={mode === 'register'}
              value={form.birth_date}
              onChange={handleChange}
              onBlur={handleBlur}
              max={new Date().toISOString().split('T')[0]}
              className={`w-full rounded-lg bg-slate-800 border px-3 py-2 focus:outline-none focus:ring-2 transition-colors ${
                errors.birth_date && touched.birth_date
                  ? 'border-red-500 focus:ring-red-500'
                  : 'border-slate-700 focus:ring-purple-500'
              }`}
            />
            {errors.birth_date && touched.birth_date && (
              <p className="text-red-400 text-xs mt-1">{errors.birth_date}</p>
            )}
            <p className="text-xs text-slate-500 mt-1">Используется для более точной интерпретации</p>
          </div>
        </>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 py-3 rounded-lg font-medium hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin">⏳</span>
            {mode === 'login' ? 'Вход...' : 'Регистрация...'}
          </span>
        ) : (
          mode === 'login' ? 'Войти в сонник' : 'Зарегистрироваться'
        )}
      </button>

      <p className="text-xs text-center text-slate-500">
        Продолжая, вы соглашаетесь с обработкой персональных данных
      </p>
    </form>
  )
}
