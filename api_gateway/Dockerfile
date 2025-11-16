# Minimal Dockerfile for api_gateway
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code/api_gateway
COPY . /code/api_gateway
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/code

CMD ["uvicorn", "api_gateway.app.main:app", "--host", "0.0.0.0"]
