FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Hugging Face Spaces use port 7860 by default
EXPOSE 7860

# Start the application
# Load root ``app.py`` first so a stale ``server/app.py`` on HF cannot break startup.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
