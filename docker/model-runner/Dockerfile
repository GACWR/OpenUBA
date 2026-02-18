FROM python:3.9-slim

# install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# set working directory
WORKDIR /app

# install python dependencies from root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# install model-runner specific requirements
COPY docker/model-runner/requirements.txt /tmp/model-runner-requirements.txt
RUN pip install --no-cache-dir -r /tmp/model-runner-requirements.txt || true

# copy runner script
COPY docker/model-runner/runner.py ./runner.py

# create non-root user
RUN groupadd -r modelrunner && useradd -r -g modelrunner -u 1000 modelrunner

# create model directory with proper permissions
RUN mkdir -p /model && chown -R modelrunner:modelrunner /model /app

# switch to non-root user
USER modelrunner

# set entrypoint
ENTRYPOINT ["python", "runner.py"]

