FROM python:3.11.11-slim

# Set working directory
WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Setting up Poetry (without creating a virtual environment)
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy project file
COPY . .

# Port 3000 is open
EXPOSE 3000

# run command
CMD ["python", "django-project/manage.py", "runserver", "0.0.0.0:3000"]
