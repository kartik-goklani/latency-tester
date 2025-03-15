import subprocess
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import socket
import time
import asyncio
import uvicorn

app = FastAPI()

# ✅ Enable CORS for WebSockets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def tcp_ping(host, port=80, timeout=3):
    """
    Attempts a TCP connection to estimate latency.
    Uses ICMP ping for localhost (127.0.0.1).
    """
    if host == "127.0.0.1":
        try:
            result = subprocess.run(["ping", "-c", "1", "127.0.0.1"], capture_output=True, text=True)
            if "time=" in result.stdout:
                latency = float(result.stdout.split("time=")[1].split()[0])
                return latency, "localhost"
            else:
                return "Unreachable", "Unknown"
        except Exception:
            return "Unreachable", "Unknown"
    
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout):
            latency = round((time.time() - start) * 1000, 3)
        try:
            domain_name = socket.gethostbyaddr(host)[0]
        except socket.herror:
            domain_name = "Unknown"
        return latency, domain_name
    except Exception:
        return "Unreachable", "Unknown"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time network latency testing.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            hosts = data.split(',')  
            results = {}
            for host in hosts:
                latency, domain_name = tcp_ping(host.strip(), 443)
                results[host.strip()] = {"latency": latency, "domain": domain_name}
            print(f"Sending results: {results}")
            await websocket.send_json(results)
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
