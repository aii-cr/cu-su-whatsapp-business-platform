# Dockerfile

# Use a lightweight Python 3.10 image
FROM python:3.10-slim

# Install essential packages (tzdata & supervisor)
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    tzdata \
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set timezone to America/Costa_Rica
ENV TZ=America/Costa_Rica
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create a working directory
WORKDIR /whatsapp_backend

COPY . /whatsapp_backend

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]