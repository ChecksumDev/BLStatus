FROM alpine:latest

LABEL maintainer="Checksum"
LABEL description="BLStatus is a simple Discord bot that shows the status of BeatLeader."
LABEL repository="https://github.com/ChecksumDev/BLStatus"
LABEL version="0.0.0"

# Install Python LTS and pip
RUN apk add --no-cache python3 py3-pip

# App directory
WORKDIR /app

# Create a user
RUN adduser -D blstatus && chown -R blstatus /app

# Switch to user
USER blstatus

# Copy requirements.txt
COPY requirements.txt .

# Install requirements
RUN pip3 install -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy app
COPY . .

# Run app
CMD ["python3", "src/main.py"]
