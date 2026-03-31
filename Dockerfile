FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV WORKERS=1

# Expose port (HF Spaces standard)
EXPOSE 7860

# Run server
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
