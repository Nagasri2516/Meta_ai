FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set unbuffered Python output
ENV PYTHONUNBUFFERED=1

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the server
CMD ["python", "server/app.py"]