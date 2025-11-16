FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем системные зависимости для pydub (ffmpeg) и других библиотек
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code/chat_service
COPY . /code/chat_service
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/code

CMD ["uvicorn", "chat_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
