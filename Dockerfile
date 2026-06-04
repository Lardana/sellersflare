FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY docs ./docs
COPY static ./static

EXPOSE 8080

CMD ["uvicorn", "sellersflare.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
