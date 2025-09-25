#!/usr/bin/env python3
"""
Script để chạy IoT Backend API và mở giao diện test
"""
import subprocess
import webbrowser
import time
import os
import sys
import threading
from pathlib import Path

def run_backend():
    """Chạy FastAPI backend server"""
    print("🚀 Starting IoT Backend API server...")
    try:
        # Chạy uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def open_frontend():
    """Mở giao diện test trong trình duyệt"""
    print("⏳ Waiting for server to start...")
    time.sleep(3)  # Đợi server khởi động
    
    # Đường dẫn đến file HTML
    current_dir = Path(__file__).parent
    html_file = current_dir / "frontend_test.html"
    
    if html_file.exists():
        print("🌐 Opening test interface in browser...")
        webbrowser.open(f"file://{html_file.absolute()}")
    else:
        print("❌ frontend_test.html not found!")

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 IoT Backend API Tester")
    print("=" * 60)
    print()
    
    # Kiểm tra file main.py
    if not os.path.exists("app/main.py"):
        print("❌ app/main.py not found!")
        print("Please run this script from the iot-backend directory")
        return
    
    # Kiểm tra requirements
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        return
    
    print("📋 Available commands:")
    print("1. Start backend server only")
    print("2. Start backend + open frontend")
    print("3. Install dependencies")
    print("4. Exit")
    print()
    
    while True:
        try:
            choice = input("Choose option (1-4): ").strip()
            
            if choice == "1":
                print("\n🚀 Starting backend server...")
                print("📝 Open http://localhost:8000/docs for API documentation")
                print("⏹️  Press Ctrl+C to stop server")
                print()
                run_backend()
                break
                
            elif choice == "2":
                print("\n🚀 Starting backend server + frontend...")
                
                # Chạy backend trong thread riêng
                backend_thread = threading.Thread(target=run_backend, daemon=True)
                backend_thread.start()
                
                # Mở frontend
                open_frontend()
                
                print("\n📝 Backend running at: http://localhost:8000")
                print("🌐 Frontend opened in browser")
                print("⏹️  Press Ctrl+C to stop server")
                print()
                
                # Đợi user dừng server
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n⏹️  Server stopped by user")
                    break
                    
            elif choice == "3":
                print("\n📦 Installing dependencies...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
                    print("✅ Dependencies installed successfully!")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Error installing dependencies: {e}")
                print()
                
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice! Please choose 1-4")
                print()
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

if __name__ == "__main__":
    main()