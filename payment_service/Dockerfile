FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code/payment_service
COPY . /code/payment_service
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/code

CMD ["uvicorn", "payment_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
