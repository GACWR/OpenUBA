FROM python:3.9-slim

# set working directory
WORKDIR /app

# install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    nodejs \
    npm \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install postgraphile globally
RUN npm install -g postgraphile

# copy application code
COPY core/ ./core/
COPY scripts/ ./scripts/
COPY test_datasets/ ./test_datasets/

# set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://openuba:openuba@postgres:5432/openuba

# expose port
EXPOSE 8000

# run application
CMD ["uvicorn", "core.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]

