from __future__ import annotations

import base64
import logging
import wave
from io import BytesIO
from typing import Optional

try:
    import speech_recognition as sr  # type: ignore
except ImportError:  # pragma: no cover
    sr = None

try:
    from gtts import gTTS  # type: ignore
except ImportError:  # pragma: no cover
    gTTS = None

try:
    from pydub import AudioSegment  # type: ignore
except ImportError:  # pragma: no cover
    AudioSegment = None

logger = logging.getLogger(__name__)


def _convert_to_wav(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Конвертирует аудио в формат WAV для распознавания речи."""
    if AudioSegment is None:
        # Если pydub недоступен, пытаемся использовать как есть
        return audio_bytes
    
    try:
        # Пытаемся определить формат по заголовку
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        # Конвертируем в моно, 16kHz, 16-bit
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_sample_width(2)  # 16-bit
        
        wav_buffer = BytesIO()
        audio.export(wav_buffer, format="wav")
        return wav_buffer.getvalue()
    except Exception as e:
        logger.warning(f"Не удалось конвертировать аудио: {e}, используем как есть")
        return audio_bytes


def _ensure_wav_format(audio_bytes: bytes) -> bytes:
    """Проверяет и конвертирует аудио в правильный WAV формат для speech_recognition."""
    # Проверяем, является ли это уже WAV файлом
    if audio_bytes[:4] == b'RIFF' and b'WAVE' in audio_bytes[:12]:
        # Это WAV файл, проверяем параметры
        try:
            with wave.open(BytesIO(audio_bytes)) as wav_file:
                # Если параметры подходят, возвращаем как есть
                if wav_file.getnchannels() == 1 and wav_file.getframerate() >= 16000:
                    return audio_bytes
        except Exception:
            pass
    
    # Конвертируем в правильный формат
    return _convert_to_wav(audio_bytes)


def transcribe_audio(audio_base64: str) -> str:
    """
    Распознает речь из аудио в формате base64.
    
    Поддерживает различные форматы аудио (WAV, MP3, OGG, FLAC и др.)
    и автоматически конвертирует их в нужный формат.
    """
    if not sr:
        logger.error("speech_recognition не установлен")
        return "Распознавание речи недоступно. Установите библиотеку SpeechRecognition."
    
    try:
        # Декодируем base64
        audio_bytes = base64.b64decode(audio_base64)
        if not audio_bytes:
            return "Пустой аудиофайл."
        
        # Конвертируем в WAV формат, если нужно
        wav_audio = _ensure_wav_format(audio_bytes)
        
        # Распознаем речь
        recognizer = sr.Recognizer()
        
        # Используем AudioData напрямую, если это возможно
        try:
            # Пытаемся открыть как файл
            with sr.AudioFile(BytesIO(wav_audio)) as source:  # type: ignore[arg-type]
                # Настраиваем распознаватель для шумной среды
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
        except Exception as e:
            logger.warning(f"Не удалось открыть как AudioFile: {e}, пробуем напрямую")
            # Пытаемся использовать напрямую
            try:
                import wave
                with wave.open(BytesIO(wav_audio)) as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    audio_data = wav_file.readframes(frames)
                    audio = sr.AudioData(audio_data, sample_rate, 2)  # 2 = 16-bit
            except Exception as e2:
                logger.error(f"Не удалось обработать аудио: {e2}")
                return "Не удалось обработать аудиофайл. Проверьте формат."
        
        # Распознаем с помощью Google Speech Recognition
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            logger.info(f"Распознан текст: {text[:50]}...")
            return text
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition не смог распознать речь")
            return "Не удалось распознать речь. Убедитесь, что аудио содержит четкую речь."
        except sr.RequestError as e:
            logger.error(f"Ошибка запроса к Google Speech Recognition: {e}")
            return "Ошибка подключения к сервису распознавания речи. Попробуйте позже."
        except Exception as e:
            logger.error(f"Неожиданная ошибка распознавания: {e}", exc_info=True)
            return "Произошла ошибка при распознавании речи."
            
    except base64.binascii.Error:
        logger.error("Неверный формат base64")
        return "Неверный формат аудио данных (base64)."
    except Exception as e:
        logger.error(f"Критическая ошибка в transcribe_audio: {e}", exc_info=True)
        return "Произошла критическая ошибка при обработке аудио."


def synthesize_speech(text: str, lang: str = "ru", slow: bool = False) -> str:
    """
    Синтезирует речь из текста и возвращает аудио в формате base64.
    
    Args:
        text: Текст для синтеза
        lang: Язык (по умолчанию 'ru' для русского)
        slow: Медленная речь (по умолчанию False)
    
    Returns:
        base64-encoded аудио (MP3 формат)
    """
    if not text or not text.strip():
        logger.warning("Пустой текст для синтеза речи")
        return base64.b64encode(b"").decode()
    
    if not gTTS:
        logger.error("gTTS не установлен")
        # Возвращаем пустой base64 вместо ошибки
        return base64.b64encode(b"").decode()
    
    try:
        # Ограничиваем длину текста (gTTS имеет лимиты)
        max_length = 5000
        if len(text) > max_length:
            logger.warning(f"Текст слишком длинный ({len(text)} символов), обрезаем до {max_length}")
            text = text[:max_length] + "..."
        
        # Создаем TTS объект
        tts = gTTS(text=text, lang=lang, slow=slow)
        
        # Генерируем аудио в память
        audio_stream = BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)
        
        # Кодируем в base64
        audio_bytes = audio_stream.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        logger.info(f"Синтезирован аудио для текста длиной {len(text)} символов")
        return audio_base64
        
    except Exception as e:
        logger.error(f"Ошибка синтеза речи: {e}", exc_info=True)
        # Возвращаем пустой base64 вместо ошибки
        return base64.b64encode(b"").decode()
