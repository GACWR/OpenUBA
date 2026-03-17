FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir kopf kubernetes pyyaml

# Copy operator code
COPY core/operator/main.py /app/main.py
COPY core/operator/workspace_handler.py /app/workspace_handler.py
COPY core/operator/pipeline_handler.py /app/pipeline_handler.py

# Run kopf
CMD ["kopf", "run", "/app/main.py", "--verbose"]
