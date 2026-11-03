FROM python:3.12.7

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
