FROM python:3.11-slim

WORKDIR /app

# Copy the entire repo into the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Run your daily job
#CMD ["python", "$JOB_SCRIPT"]

RUN echo "JOB_SCRIPT at build time: $JOB_SCRIPT"

# Run your daily job (expanded by shell)
CMD ["sh", "-c", "python $JOB_SCRIPT"]