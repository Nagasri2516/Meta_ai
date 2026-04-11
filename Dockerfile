FROM python:3.10-slim

WORKDIR /app

# Install only what's needed
RUN pip install fastapi uvicorn pydantic

# Copy the server file
COPY server/app.py .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Run the server
CMD ["python", "app.py"]