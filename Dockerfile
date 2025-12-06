# First, build the application in the `/app` directory
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR /python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.11

WORKDIR /app

COPY ./pyproject.toml /app/pyproject.toml
COPY ./uv.lock /app/uv.lock
RUN uv sync
RUN uv export --no-hashes --no-header --no-annotate --no-dev --format requirements.txt > requirements.txt
RUN cat requirements.txt

# Use the official Python runtime image
FROM python:3.11-slim

# Create a specific user and the app directory
RUN useradd -m -r python && \
    mkdir /app && \
    chown -R python /app

# Set the working directory inside the container
WORKDIR /app

# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

# Upgrade pip
RUN pip install --upgrade pip 

# Copy the Django project  and install dependencies
COPY --from=builder /app/requirements.txt  /app/requirements.txt

# run this command to install all dependencies 
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY --chown=python:python /checklistapp/ /app/

# Collecte les fichiers statiques dans le dossier STATIC_ROOT
RUN python manage.py collectstatic --noinput

USER python

# Expose the Django port
EXPOSE 8000

# Run Django’s development server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "checklistapp.wsgi:application"]