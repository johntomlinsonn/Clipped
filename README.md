# Clipped
A tool to take in YouTube videos and generate viral short clips.

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
   STORAGE_DIR=../storage
   ```
2. To get a free Cerebras Cloud API key, sign up at https://cloud.cerebras.ai/ and copy your key from the dashboard.

## Running the server

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

The API docs will be available at: `http://127.0.0.1:8000/docs`

## Endpoints

- **POST** `/download/` - Download a video by URL
- **POST** `/transcribe/` - Transcribe a downloaded video
- **POST** `/analyze/` - Analyze a transcript for viral moments
- **POST** `/clip/` - Generate video clips from analysis JSON
- **POST** `/cleanup/` - Clear all files in storage directory
- **POST** `/full_flow/` - Run download → transcribe → analyze → clip (no cleanup)
