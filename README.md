# Clipped
A tool to take in YouTube videos and generate viral short clips.

## Quick Start

- **Run with Python**: follow the [Setup](#setup) and [Running the server](#running-the-server) sections below.
- **Run with Docker**: follow the [Docker](#docker) section below.

## Prerequisites

- Python 3.10+ installed
- Git

## Setup

1. Clone the repo:
   ```powershell
   git clone https://github.com/johntomlinsonn/Clipped.git
   cd Clipped/clipped-backend
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   # Windows (PowerShell):
   .venv/scripts/activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the `clipped-backend/` with:
   ```properties
   CEREBRAS_API_KEY=<your_api_key>
   STORAGE_DIR=./storage
   FASTAPI_HOST=127.0.0.1
   FASTAPI_PORT=8000
TMP_DIR=./tmp
   ```
2. To get a free Cerebras Cloud API key, sign up at https://cloud.cerebras.ai/ and copy your key from the dashboard.

## Running the server

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

The API docs will be available at: `http://127.0.0.1:8000/docs`

## Docker

### Environment Variables

Create or update the `.env` file in the `clipped-backend/` folder with:
```properties
CEREBRAS_API_KEY=<your_api_key>
STORAGE_DIR=./storage
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
TMP_DIR=./tmp
```

### Build & Run with Docker Compose

From the workspace root (`Clipped/`):
```powershell
docker-compose build clipped-backend
docker-compose up -d
```
This will build the image, start the container on port `8000`, and bind-mount `./storage` → `/app/storage`.

To stop and remove containers:
```powershell
docker-compose down
```

To view logs:
```powershell
docker-compose logs -f clipped-backend
```

API docs are available at: `http://localhost:8000/docs`

## Endpoints

- **POST** `/download/` - Download a video by URL
- **POST** `/transcribe/` - Transcribe a downloaded video
- **POST** `/analyze/` - Analyze a transcript for viral moments
- **POST** `/clip/` - Generate video clips from analysis JSON
- **POST** `/cleanup/` - Clear all files in storage directory
- **POST** `/full_flow/` - Run download → transcribe → analyze → clip (no cleanup)
