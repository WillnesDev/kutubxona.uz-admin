import subprocess
import threading
import time

def run_main_server():
    """Asosiy sayt serveri (port 8080)"""
    subprocess.run(['python', 'main.py'])

def run_admin_server():
    """Admin panel serveri (port 5000)"""
    time.sleep(2)
    subprocess.run(['python', 'admin.py'])

if __name__ == '__main__':
    print("🚀 Ikkala server ishga tushirilmoqda...")
    
    # Asosiy server thread
    main_thread = threading.Thread(target=run_main_server)
    main_thread.daemon = True
    main_thread.start()
    
    # Admin server thread
    admin_thread = threading.Thread(target=run_admin_server)
    admin_thread.daemon = True
    admin_thread.start()
    
    print("✅ Serverlar ishga tushdi!")
    print("🌐 Asosiy sayt: http://localhost:8080")
    print("⚙️ Admin panel: http://localhost:5000")
    print("👤 Admin login: admin / admin123")
    print("\n⏹️ To'xtatish uchun Ctrl+C bosing")
    
    try:
        main_thread.join()
        admin_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Serverlar to'xtatildi!")
