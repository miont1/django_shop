# Use the official Python slim image for a lightweight container
FROM python:3.14-slim

# Set environment variables to prevent Python from writing pyc files and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling or running dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker's build cache
COPY requirements.txt /app/

# Install the Python dependencies, gunicorn WSGI server, and whitenoise for static files
RUN pip install --no-cache-dir -r requirements.txt gunicorn whitenoise

# Copy the rest of the application code
COPY . /app/

# Change working directory to the sub-folder where manage.py is located
WORKDIR /app/django_shop

# Collect static files into the STATIC_ROOT directory
RUN python manage.py collectstatic --noinput

# Expose port 8000 to the host
EXPOSE 8000

# Run the Django application, applying database migrations first
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
