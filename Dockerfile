FROM python:3.11-slim

WORKDIR /app

# Copy the entire repo into the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Run your daily job
CMD ["python", "$JOB_SCRIPT"]