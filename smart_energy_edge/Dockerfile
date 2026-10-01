FROM python:3.11-slim

WORKDIR /app

# Докачиваем системную библиотеку для работы LightGBM
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Команда для запуска твоего сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]