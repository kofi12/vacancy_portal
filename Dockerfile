# Use a lightweight Python base image
FROM python:3.11-slim AS python-base

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2 && poetry config virtualenvs.create false

# Set the working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-interaction

# Copy application files
COPY . /app

# Expose the port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
