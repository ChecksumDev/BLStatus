LABEL maintainer="Checksum"
LABEL description="BLStatus is a simple Discord bot that shows the status of BeatLeader."
LABEL repository="https://github.com/ChecksumDev/BLStatus"
LABEL version="0.0.0"

FROM alpine:latest

# Install Python LTS and pip
RUN apk add --no-cache python3 py3-pip

# App directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install requirements
RUN pip3 install -r requirements.txt

# Copy app
COPY . .

# Run app
CMD ["python3", "app.py"]
