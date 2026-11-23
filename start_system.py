import os
import sys
import time
import subprocess
import re
import socket
import webbrowser
import signal

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FOS_DIR = os.path.join(BASE_DIR, "food-ordering-system")
BACKEND_DIR = os.path.join(FOS_DIR, "backend")
REST_DIR = os.path.join(FOS_DIR, "restaurant-web")
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_process_on_port(port):
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                subprocess.call(f"taskkill /F /PID {pid} >nul 2>&1", shell=True)
    except Exception:
        pass

def main():
    print("=" * 68)
    print("  🍱 STARTING CRAVEBITES LOCAL SYSTEM (BACKEND + CLOUDFLARE TUNNEL)")
    print("=" * 68)
    print()

    # 1. Start Backend on Port 5000 if not listening
    if not is_port_in_use(5000):
        print("[*] Starting CraveBites Flask Backend on Port 5000...")
        backend_proc = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        print("[+] Backend is already running on Port 5000.")
        backend_proc = None

    # Wait for backend to be ready
    for _ in range(15):
        if is_port_in_use(5000):
            break
        time.sleep(1)

    # 2. Start Restaurant Web on Port 5002 if not listening
    if not is_port_in_use(5002):
        print("[*] Starting CraveBites Restaurant Dashboard on Port 5002...")
        rest_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", "5002", "--bind", "127.0.0.1"],
            cwd=REST_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        print("[+] Restaurant Web is already running on Port 5002.")
        rest_proc = None

    # 3. Start Cloudflare Tunnel
    print("[*] Launching Cloudflare Wireless Tunnel (fetching public URL)...")
    tunnel_proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:5000"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    start_time = time.time()

    while time.time() - start_time < 35:
        line = tunnel_proc.stderr.readline()
        if not line:
            time.sleep(0.1)
            continue
        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        print("[!] Could not auto-detect Cloudflare URL. Please check your internet connection.")
        if tunnel_proc:
            tunnel_proc.terminate()
        return

    print("\n" + "=" * 68)
    print("  🎉 CRAVEBITES SYSTEM IS LIVE ON CLOUDFLARE!")
    print("=" * 68)
    print(f"  🌐 Public Cloudflare URL : {tunnel_url}")
    print()
    print("  📱 OPEN ON YOUR PHONES (Chrome / Safari - NO WIRE NEEDED):")
    print(f"  👉 Customer App : {tunnel_url}/app")
    print(f"  👉 Rider App    : {tunnel_url}/rider")
    print()
    print("  💻 RESTAURANT DASHBOARD (Laptop):")
    print("  👉 http://127.0.0.1:5002")
    print("=" * 68)
    print("  [Tip] On your phone, tap menu ⋮ -> 'Add to Home screen' for full screen!")
    print("  [Note] Keep this window OPEN. Press Ctrl+C to stop all servers.")
    print("=" * 68 + "\n")

    # Automatically open Restaurant Web on laptop
    try:
        webbrowser.open("http://127.0.0.1:5002")
    except Exception:
        pass

    try:
        # Keep process running and streaming tunnel status
        while True:
            line = tunnel_proc.stderr.readline()
            if tunnel_proc.poll() is not None:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[*] Stopping CraveBites servers...")
        try:
            tunnel_proc.terminate()
        except Exception:
            pass
        if backend_proc:
            try:
                backend_proc.terminate()
            except Exception:
                pass
        if rest_proc:
            try:
                rest_proc.terminate()
            except Exception:
                pass
        print("[+] CraveBites system stopped successfully.")

if __name__ == '__main__':
    main()
