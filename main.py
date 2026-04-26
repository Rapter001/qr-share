from flask import Flask
import socket
import os

app = Flask(__name__)

@app.route('/')
def home():
    return {
        'message': 'Komodo test app is running!',
        'hostname': socket.gethostname(),
        'version': os.getenv('APP_VERSION', '1.0.0')
    }

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)