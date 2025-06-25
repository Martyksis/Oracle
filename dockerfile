# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Копируем весь код проекта
COPY . .

# Команда для запуска приложения
CMD ["python", "main.py"]
