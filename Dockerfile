FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set default environment variables (can be overridden)
ENV APP_USERNAME=admin
ENV APP_PASSWORD=changeme123
ENV SECRET_KEY=your-secret-key-here-change-in-production

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Run Flask directly (no gunicorn)
CMD ["python3", "main.py"]