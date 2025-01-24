# CU-SU WhatsApp Business Platform Backend

**Built with FastAPI (v0.115.5)**, this backend provides endpoints to integrate WhatsApp Business API with a simple webhook flow to receive and respond to messages, and includes a test endpoint to send a WhatsApp template message.

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation](#installation)
- [Running with Docker](#running-with-docker)
- [Usage](#usage)
- [Logging](#logging)

---

## Features
- **Receive and log WhatsApp messages** through a configured [Meta Webhook](https://developers.facebook.com/docs/whatsapp/cloud-api).
- **Simple test endpoint** (`/whatsapp/send-test-message`) to send a WhatsApp template message.
- **Logger setup** using Python’s built-in `logging` module, with console and file outputs.
- **Flexible project structure** for future scalability (AI chatbot, additional business logic, etc.).

---

## Project Structure

A typical directory structure might look like this:

```
whatsapp_backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── whatsapp.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── utils.py
│   └── main.py
├── logs/
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

- **`app/main.py`**: Application entry point for FastAPI.
- **`app/api/routes/whatsapp.py`**: Contains WhatsApp webhook routes and a test message endpoint.
- **`app/core/logger.py`**: Sets up and configures the logger.
- **`app/core/config.py`**: Loads environment variables from `.env`.
- **`app/core/utils.py`**: Utility functions (e.g., sending WhatsApp messages).
- **`logs/`**: Directory for log files.

---

## Prerequisites

1. **Python 3.10+**  
2. **Meta (Facebook) Developer Account** with WhatsApp Business Cloud API access.
3. **.env file** containing necessary environment variables (e.g., tokens, phone number IDs).
4. (Optional) **Docker** and **Docker Compose** for containerization.

---

## Environment Variables

Create a `.env` file in the project root with values appropriate for your environment. For example:

```bash
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_VERIFY_TOKEN=verify_token_string
WHATSAPP_BUSINESS_ID=526160010584086
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
ENVIRONMENT=development
```

> **Important**: Never commit `.env` with real credentials to source control. 

---

## Installation

If you prefer running the project **locally** without Docker:

1. **Clone** this repository:
   ```bash
   git clone https://github.com/your-org/whatsapp_backend.git
   cd whatsapp_backend
   ```
2. **Create/Activate** a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```
3. **Install** dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Run** the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

Your FastAPI app should now be available at `http://localhost:8000`.

---

## Running with Docker

We provide a **`Dockerfile`** and **`docker-compose.yml`** for easy containerization.

1. **Build** the image:
   ```bash
   docker-compose build
   ```
   - This uses the Dockerfile in the current directory.

2. **Start** the container:
   ```bash
   docker-compose up -d
   ```
   - The app will run on container port 8000. 
   - In the compose file, it’s mapped to **50337** on your host, so you can reach it at `http://localhost:50337/`.

3. **Container Management**:
   - **Check Logs**: `docker-compose logs -f whatsapp_platform`
   - **Stop**: `docker-compose down`

### Docker Compose Overview

A minimal `docker-compose.yml` includes:
```yaml
version: '3.8'

services:
  whatsapp_platform:
    container_name: whatsapp_platform
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "50337:8000"
    restart: unless-stopped
    env_file:
      - .env
```
> - Maps port **50337** (on your machine) to port **8000** (inside the container).
> - Uses `.env` for environment variables.

---

## Usage

1. **Webhook Setup**:  
   - In Meta’s Developer Portal, configure your webhook callback URL as `https://your-domain/whatsapp/webhook`.  
   - Provide your **verify token** (must match `WHATSAPP_VERIFY_TOKEN` in `.env`).

2. **Verify Endpoint**:  
   - Handles GET requests to `/whatsapp/webhook` for verification.  

3. **Receive Messages**:  
   - Postbacks from Meta (Facebook) will come to `/whatsapp/webhook` as a **POST** request.  
   - The application logs and can auto-reply with a WhatsApp template if you choose.

4. **Send Test Message**:  
   - Hit `GET http://localhost:50337/whatsapp/send-test-message` (in Docker)  
   - This triggers a template message to the test phone number **50684716592** (hardcoded in the route, or as you configure).

---

## Logging

- Logs are written to `logs/whatsapp.log` and also printed to stdout. 
- Adjust `logger` in `app/core/logger.py` as needed for your environment or log rotation preferences.
