FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn pydantic

# Copy the server file
COPY server/app.py .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "app.py"]