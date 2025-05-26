FROM python:3.11-slim

# Install system dependencies (including Tesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
