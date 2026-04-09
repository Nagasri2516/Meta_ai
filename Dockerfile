FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install your package in development mode
RUN pip install -e .

EXPOSE 8000

# Update CMD to use the correct module path
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]