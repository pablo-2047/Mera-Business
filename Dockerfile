FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files (excludes .git, venv, etc.)
COPY app.py .
COPY database.py .
COPY intent_router.py .
COPY simple_intent_router.py .
COPY chat_ui.py .
COPY dashboard.py .
COPY pdf_generator.py .
COPY generate_sample_data.py .

# Create necessary directories
RUN mkdir -p /app/invoices /app/chat_media /app/logs

# Initialize database with schema and generate sample data
RUN python -c "from database import init_database; init_database()" && \
    python generate_sample_data.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
