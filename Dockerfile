# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on (Railway will set PORT env var at runtime)
EXPOSE 8000

# Health check using python requests (use PORT env var)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; import os; requests.get(f'http://localhost:{os.getenv(\"PORT\", \"8000\")}/', timeout=5)" || exit 1

# Command to run the application (use our main.py which respects PORT env var)
CMD ["python", "main.py"]
