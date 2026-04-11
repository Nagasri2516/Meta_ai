FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install your package
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Health check for Hugging Face
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

# Expose port
EXPOSE 7860

# Run the server
CMD ["python", "-u", "server/app.py"]