# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=false
ENV DJANGO_SECRET_KEY="dummy_secret_key_for_build_only"

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN cd backend && python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Command to run Gunicorn
WORKDIR /app/backend
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
