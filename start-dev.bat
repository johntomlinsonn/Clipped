@echo off
echo 🚀 Starting Clipped Development Environment...

echo 📡 Starting Backend API (Port 8000)...
cd clipped-backend
start "Backend" python app.py

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo 🌐 Starting Frontend (Port 3000)...
cd ..\clipped-frontend
start "Frontend" npm run dev

echo ✅ Development environment started!
echo 📡 Backend API: http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo 📖 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause > nul
