from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote
import json
from pymongo import MongoClient
import os

class CarRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def _normalize_text(self, text):
        return unquote(text).strip().lower()

    def _get_car_data(self, brand, model):
        client = MongoClient('mongodb+srv://Siri_varshini:sahi2002@cluster0.ikhcjpi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        db = client['CarData']
        cars = db['cars']
        
        return cars.find_one({
            'brand': {'$regex': f'^{brand}$', '$options': 'i'},
            'model': {'$regex': f'^{model}$', '$options': 'i'}
        }, {'_id': 0, 'pressure': 1, 'temperature': 1, 'load': 1, 'treadDepth': 1})

    def do_HEAD(self):
        # Implement do_HEAD to avoid 501 errors on HEAD requests
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = [p for p in parsed_path.path.split('/') if p]  # Remove empty parts
        
        try:
            if len(path_parts) == 0:
                # Handle root path /
                self._set_headers(200, 'text/html')
                self.wfile.write(b"<html><body><h1>Welcome to Car API Server</h1></body></html>")
                return

            if len(path_parts) >= 2 and path_parts[0] == 'api':
                if path_parts[1] == 'brands' and len(path_parts) == 2:
                    client = MongoClient('mongodb+srv://Siri_varshini:sahi2002@cluster0.ikhcjpi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
                    brands = client['CarData']['cars'].distinct('brand')
                    self._set_headers()
                    self.wfile.write(json.dumps(brands).encode())

                elif path_parts[1] == 'models' and len(path_parts) == 3:
                    brand = self._normalize_text(path_parts[2])
                    client = MongoClient('mongodb+srv://Siri_varshini:sahi2002@cluster0.ikhcjpi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
                    models = client['CarData']['cars'].distinct('model', {
                        'brand': {'$regex': f'^{brand}$', '$options': 'i'}
                    })
                    self._set_headers()
                    self.wfile.write(json.dumps(models).encode())

                elif path_parts[1] == 'car' and len(path_parts) == 4:
                    brand = self._normalize_text(path_parts[2])
                    model = self._normalize_text(path_parts[3])
                    car = self._get_car_data(brand, model)
                    
                    if car:
                        self._set_headers()
                        self.wfile.write(json.dumps(car).encode())
                    else:
                        self._set_headers(404)
                        self.wfile.write(json.dumps({
                            'error': 'Car not found',
                            'requested_brand': unquote(path_parts[2]),
                            'requested_model': unquote(path_parts[3])
                        }).encode())

                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())
        
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())

def run(server_class=HTTPServer, handler_class=CarRequestHandler):
    port = int(os.environ.get('PORT', 5050))  # Use environment variable PORT or default 5050
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
