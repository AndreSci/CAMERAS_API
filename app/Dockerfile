FROM python:3.10

WORKDIR /app

COPY . .

EXPOSE 8093

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    libavcodec-dev \
    libavformat-dev \
    libavdevice-dev \
    libgl1 \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

CMD ["python", "main.py" ]