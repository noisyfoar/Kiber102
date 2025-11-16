FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code/telegram_bot
COPY . /code/telegram_bot
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/code

CMD ["python", "-u", "-m", "telegram_bot.bot.main"]
