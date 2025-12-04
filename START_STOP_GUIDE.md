# 🚀 Start & Stop Guide - AI Workload Routing System

Complete guide for starting and stopping the backend and frontend services.

---

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ **Python 3.8+** installed (`python3 --version`)
- ✅ **Node.js 16+** installed (`node --version`)
- ✅ **npm** installed (`npm --version`)

---

## 🟢 Starting the Services

### Method 1: Quick Start (Recommended)

#### Start Backend
```bash
# From project root directory
python3 start_backend.py
```

This script will:
- ✅ Check Python version
- ✅ Install dependencies if missing
- ✅ Start the backend server on http://localhost:8000

#### Start Frontend (New Terminal)
```bash
# Open a new terminal window
cd frontend
npm start
```

This will:
- ✅ Start the React development server
- ✅ Open http://localhost:3000 in your browser
- ✅ Enable hot-reload for development

---

### Method 2: Manual Start

#### Backend (Terminal 1)
```bash
# Navigate to backend directory
cd backend

# Install dependencies (first time only)
python3 -m pip install --user -r requirements.txt

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (Terminal 2)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm start
```

---

## 🔴 Stopping the Services

### Stop Backend

**Method 1: Keyboard Interrupt**
```bash
# In the terminal running the backend, press:
Ctrl + C
```

**Method 2: Kill Process by Port**
```bash
# Find the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or on Linux/macOS:
kill -9 $(lsof -t -i:8000)
```

**Method 3: Kill by Process Name**
```bash
# Find and kill uvicorn processes
pkill -f uvicorn

# Or more specifically:
ps aux | grep uvicorn
kill -9 <PID>
```

---

### Stop Frontend

**Method 1: Keyboard Interrupt**
```bash
# In the terminal running the frontend, press:
Ctrl + C
```

**Method 2: Kill Process by Port**
```bash
# Find the process using port 3000
lsof -ti:3000 | xargs kill -9

# Or on Linux/macOS:
kill -9 $(lsof -t -i:3000)
```

**Method 3: Kill by Process Name**
```bash
# Find and kill node processes
pkill -f "react-scripts start"

# Or more specifically:
ps aux | grep "react-scripts"
kill -9 <PID>
```

---

## 🔄 Restart Services

### Restart Backend
```bash
# Stop the backend (Ctrl+C or kill process)
# Then start again:
python3 start_backend.py
```

### Restart Frontend
```bash
# Stop the frontend (Ctrl+C or kill process)
# Then start again:
cd frontend
npm start
```

---

## ✅ Verify Services are Running

### Check Backend Status
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"...","services":{...}}
```

### Check Frontend Status
```bash
# Open in browser:
open http://localhost:3000

# Or check if port is in use:
lsof -i:3000
```

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Issue: Port 8000 already in use**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
# Then restart
python3 start_backend.py
```

**Issue: Missing dependencies**
```bash
cd backend
python3 -m pip install --user -r requirements.txt --force-reinstall
```

**Issue: Python version too old**
```bash
# Check version
python3 --version
# Upgrade Python to 3.8+ if needed
```

---

### Frontend Won't Start

**Issue: Port 3000 already in use**
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9
# Then restart
cd frontend && npm start
```

**Issue: Node modules corrupted**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**Issue: Node.js version too old**
```bash
# Check version
node --version
# Upgrade Node.js to 16+ if needed
```

---

## 📊 Service URLs

Once both services are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Web interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System health status |
| **Stats** | http://localhost:8000/api/v1/stats | System statistics |

---

## 🔍 Check Running Processes

### List All Related Processes
```bash
# Check backend processes
ps aux | grep uvicorn

# Check frontend processes
ps aux | grep "react-scripts"

# Check ports in use
lsof -i:8000  # Backend
lsof -i:3000  # Frontend
```

---

## 💡 Quick Reference

### Start Everything
```bash
# Terminal 1: Backend
python3 start_backend.py

# Terminal 2: Frontend
cd frontend && npm start
```

### Stop Everything
```bash
# Press Ctrl+C in both terminals
# Or kill all processes:
pkill -f uvicorn && pkill -f "react-scripts"
```

### Clean Restart
```bash
# Stop all services
pkill -f uvicorn && pkill -f "react-scripts"

# Clear ports
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Restart
python3 start_backend.py &
cd frontend && npm start
```

---

## 📝 Notes

- **Development Mode**: Both services run with hot-reload enabled
- **Logs**: Check terminal output for errors and status messages
- **Configuration**: Edit `config/config.yaml` for backend settings
- **Environment**: Frontend uses `.env` file for configuration (if present)

---

**Need Help?** Check the main [README.md](README.md) for more detailed documentation.

