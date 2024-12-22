from jinja2 import Environment, FileSystemLoader
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import json
from datetime import datetime
from urllib.parse import parse_qs

# Конфігурація
HOST = '0.0.0.0'
PORT = 3000
DATA_FILE = 'storage/data.json'

# Ініціалізація Jinja2
BASE_DIR = os.path.dirname(__file__)
TEMPLATES_PATH = os.path.join(BASE_DIR, 'templates')
STATIC_PATH = os.path.join(BASE_DIR, 'static')

env = Environment(loader=FileSystemLoader(TEMPLATES_PATH))


# Перевірка існування необхідних файлів і папок
if not os.path.exists('storage'):
    os.makedirs('storage')
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)


class CustomHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Клас для обробки HTTP-запитів.
    """

    def do_GET(self):
        routes = {
            '/': 'index.html.jinja2',
            '/message.html': 'message.html.jinja2',
            '/read': 'read.html.jinja2',
        }

        if self.path in routes:
            template = env.get_template(routes[self.path])
            if self.path == '/read':
                with open(DATA_FILE, 'r') as f:
                    messages = json.load(f)
                # Сортуємо повідомлення за часом у зворотному порядку
                sorted_messages = dict(sorted(messages.items(), key=lambda x: x[0], reverse=True))
                content = template.render(messages=sorted_messages)
            else:
                content = template.render()
            self._send_response(200, content)
        elif self.path.startswith('/static/'):
            self._serve_static()
        else:
            template = env.get_template('error.html.jinja2')
            content = template.render()
            self._send_response(404, content)

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse_qs(post_data.decode('utf-8'))

            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]

            if username and message:
                with open(DATA_FILE, 'r+') as f:
                    stored_data = json.load(f)
                    timestamp = datetime.now().isoformat()
                    stored_data[timestamp] = {"username": username, "message": message}
                    f.seek(0)
                    json.dump(stored_data, f, indent=4)

                self._redirect('/')
            else:
                self._send_response(400, 'Bad Request: Missing username or message')
        else:
            self._send_response(404, 'Not Found')

    def _send_response(self, status, content):
        """
        Відправка HTML-відповіді клієнту.
        """
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _serve_static(self):
        """
        Обробка статичних файлів.
        """
        file_path = os.path.join(STATIC_PATH, os.path.basename(self.path))
        if os.path.exists(file_path):
            self.send_response(200)
            if file_path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif file_path.endswith('.png'):
                self.send_header('Content-type', 'image/png')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self._send_response(404, 'Static File Not Found')

    def _redirect(self, location):
        """
        Перенаправлення клієнта на іншу сторінку.
        """
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()


# Запуск сервера у багатопоточному режимі
if __name__ == '__main__':
    try:
        httpd = HTTPServer((HOST, PORT), CustomHTTPRequestHandler)
        server = Thread(target=httpd.serve_forever)
        server.start()
        print(f"🚀 Server is running on http://{HOST}:{PORT}")
    except KeyboardInterrupt:
        print("\n🛑 Server is stopping...")
        httpd.shutdown()
        server.join()
        print("✅ Server has been stopped.")
