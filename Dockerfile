FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (app uses 9000)
EXPOSE 9000

# Run with auto-reload for development
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
