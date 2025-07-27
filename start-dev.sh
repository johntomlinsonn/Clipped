#!/bin/bash

# Start the Clipped development environment

echo "🚀 Starting Clipped Development Environment..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start Backend
echo "📡 Starting Backend API (Port 8000)..."
cd clipped-backend
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Frontend
echo "🌐 Starting Frontend (Port 3000)..."
cd ../clipped-frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Development environment started!"
echo "📡 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait
