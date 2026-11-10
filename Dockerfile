# Use the official Python slim image for a lightweight container
FROM python:3.14-slim

# Install uv from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables:
# - PYTHONDONTWRITEBYTECODE & PYTHONUNBUFFERED: Standard Python container settings
# - UV_COMPILE_BYTECODE: Compile Python source files to bytecode after installation
# - UV_LINK_MODE: Copy files instead of hardlinking (ensures compatibility across Docker filesystems)
# - PATH: Add virtual environment binaries to PATH so python/manage.py/gunicorn run seamlessly
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling or running dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies into /app/.venv using the lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

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
