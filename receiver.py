from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class DataReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Boot #{data['boot']}: {data['cm']} cm ({data['inches']} inches)")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), DataReceiver)
    print("Server listening on port 8080...")
    print("Waiting for ESP32 data...\n")
    server.serve_forever()
