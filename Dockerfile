FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

# Give read/write permissions to the /app directory 
# This is CRITICAL for Hugging Face Spaces so your SQLite database (database.db) 
# and FAISS vector files can be created and modified by the non-root user.
RUN chmod -R 777 /app

# Start the Flask app using Gunicorn bound to port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "app:app"]
