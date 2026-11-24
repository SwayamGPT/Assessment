import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STUDENTS = [
    {"id": 1, "name": "Aarav", "subject": "Mathematics", "score": 88},
    {"id": 2, "name": "Diya", "subject": "Mathematics", "score": 92},
    {"id": 3, "name": "Rohan", "subject": "Mathematics", "score": 67},
    {"id": 4, "name": "Ananya", "subject": "Mathematics", "score": 75},
    {"id": 5, "name": "Vivaan", "subject": "Mathematics", "score": 54},
    {"id": 6, "name": "Isha", "subject": "Mathematics", "score": 81},
    {"id": 7, "name": "Kabir", "subject": "Mathematics", "score": 96},
    {"id": 8, "name": "Meera", "subject": "Mathematics", "score": 70},
    {"id": 9, "name": "Arjun", "subject": "Mathematics", "score": 62},
    {"id": 10, "name": "Sneha", "subject": "Mathematics", "score": 85},
]

PATH = "/api/students"


class ScoresHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/") != PATH:
            self._send(404, {"error": "not found"})
            return
        self._send(200, {"students": STUDENTS})

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):   # keep console output clean
        pass


def start_in_background(host="127.0.0.1", port=0):
    """Start the API on a free port in a daemon thread; return (server, url)."""
    server = ThreadingHTTPServer((host, port), ScoresHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{host}:{server.server_port}{PATH}"


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ScoresHandler)
    print(f"Serving student scores at http://127.0.0.1:8000{PATH} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
