FROM python:3.10

WORKDIR /app

COPY . .

# 🔥 upgrade pip first
RUN pip install --upgrade pip

# 🔥 install dependencies (force)
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 EXTRA SAFETY (force install openenv)
RUN pip install openenv-core

EXPOSE 8000

CMD ["uvicorn", "server.app", "--host", "0.0.0.0", "--port", "8000"]