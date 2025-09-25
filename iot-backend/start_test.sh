#!/bin/bash

echo "========================================"
echo "    IoT Backend API Tester"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python3 and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ app/main.py not found"
    echo "Please run this script from the iot-backend directory"
    exit 1
fi

# Function to show menu
show_menu() {
    echo "📋 Available options:"
    echo "1. Install dependencies"
    echo "2. Start backend server"
    echo "3. Start backend + open frontend"
    echo "4. Exit"
    echo
}

# Function to install dependencies
install_deps() {
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dependencies installed successfully!"
    else
        echo "❌ Error installing dependencies"
    fi
    echo
}

# Function to start backend only
start_backend() {
    echo "🚀 Starting backend server..."
    echo "📝 API Documentation: http://localhost:8000/docs"
    echo "⏹️  Press Ctrl+C to stop server"
    echo
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Function to start backend + frontend
start_with_frontend() {
    echo "🚀 Starting backend server + frontend..."
    echo "⏳ Starting server in background..."
    
    # Start server in background
    python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Open frontend in browser
    echo "🌐 Opening test interface..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "frontend_test.html"
    elif command -v open &> /dev/null; then
        open "frontend_test.html"
    else
        echo "Please open frontend_test.html in your browser"
    fi
    
    echo
    echo "📝 Backend running at: http://localhost:8000"
    echo "🌐 Frontend opened in browser"
    echo "⏹️  Press any key to stop server"
    echo
    read -n 1 -s
    
    # Kill the server process
    kill $SERVER_PID 2>/dev/null
    echo "⏹️  Server stopped"
    echo
}

# Main menu loop
while true; do
    show_menu
    read -p "Choose option (1-4): " choice
    
    case $choice in
        1)
            install_deps
            ;;
        2)
            start_backend
            ;;
        3)
            start_with_frontend
            ;;
        4)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice! Please choose 1-4"
            echo
            ;;
    esac
done