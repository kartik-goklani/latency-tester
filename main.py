import subprocess
from fastapi import FastAPI, WebSocket
import socket
import time
import asyncio
import uvicorn

app = FastAPI()

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
    
    Listens for incoming messages containing comma-separated hostnames/IPs,
    pings each one using TCP, and sends back their latency in milliseconds along with resolved domain names.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            hosts = data.split(',')  # Allow multiple hosts
            results = {}
            for host in hosts:
                latency, domain_name = tcp_ping(host.strip(), 443)  # Testing HTTPS (port 443)
                results[host.strip()] = {"latency": latency, "domain": domain_name}
            print(f"Sending results: {results}")  # Debugging output
            await websocket.send_json(results)
            await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")  # Debugging output
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
