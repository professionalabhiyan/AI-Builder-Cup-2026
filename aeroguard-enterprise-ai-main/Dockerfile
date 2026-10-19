FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies including gunicorn and whitenoise
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise

# Copy the entire project repository into the container
COPY . .

# Expose port 8080 as required by Cloud Run
EXPOSE 8080

# Run migrations, collect static assets, and start Gunicorn server with pythonpath
CMD python backend/manage.py migrate && python backend/manage.py collectstatic --noinput && gunicorn --pythonpath backend aeroguard_backend.wsgi:application --bind 0.0.0.0:8080
