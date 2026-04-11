FROM python:3.10

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install your package in development mode
# This makes 'smart_waste_env' importable
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Expose the port
EXPOSE 7860

# Run the server
CMD ["python", "server/app.py"]