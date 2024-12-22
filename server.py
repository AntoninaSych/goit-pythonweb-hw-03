import http.server
import socketserver
import urllib.parse
import json
from datetime import datetime
import os

# Параметри сервера
PORT = 3000
DATA_FILE = 'storage/data.json'

# Перевірка наявності data.json
if not os.path.exists('storage'):
    os.makedirs('storage')
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """
        Обробка GET-запитів.
        """
        if self.path == '/':
            self.path = 'index.html'
        elif self.path == '/message.html':
            self.path = 'message.html'
        elif self.path == '/error.html':
            self.path = 'error.html'
        elif self.path == '/read':
            self.show_messages()
            return
        elif self.path in ['/style.css', '/logo.png']:
            pass  # Обробка статичних файлів
        else:
            self.path = 'error.html'
            self.send_response(404)

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        """
        Обробка POST-запитів для форми.
        """
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]

            if username and message:
                with open(DATA_FILE, 'r+') as f:
                    stored_data = json.load(f)
                    timestamp = datetime.now().isoformat()
                    stored_data[timestamp] = {"username": username, "message": message}
                    f.seek(0)
                    json.dump(stored_data, f, indent=4)

                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_error(400, "Both 'username' and 'message' fields are required")
        else:
            self.send_error(404)

    def show_messages(self):
        """
        Відображення збережених повідомлень зі стилями.
        """
        with open(DATA_FILE, 'r') as f:
            messages = json.load(f)

        response_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Messages</title>
            <link rel="stylesheet" href="/style.css">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <header>
                <nav class="navbar navbar-expand navbar-dark bg-dark">
                    <div class="container-fluid">
                        <a class="navbar-brand" href="/">
                            <img src="/logo.png" alt="logo" height="30">
                        </a>
                        <ul class="navbar-nav me-auto">
                            <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
                            <li class="nav-item"><a class="nav-link" href="/message.html">Send Message</a></li>
                            <li class="nav-item"><a class="nav-link active" href="/read">View Messages</a></li>
                        </ul>
                    </div>
                </nav>
            </header>
            <main class="container mt-4">
                <h1 class="text-center">Saved Messages</h1>
                <ul class="list-group">
        """
        for timestamp, msg in messages.items():
            response_content += f"""
            <li class="list-group-item">
                <strong>{msg['username']}</strong>: {msg['message']}
                <small class="text-muted d-block">({timestamp})</small>
            </li>
            """

        response_content += """
                </ul>
            </main>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response_content.encode('utf-8'))


# Запуск сервера
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
