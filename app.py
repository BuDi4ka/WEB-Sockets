import socket
import json
from threading import Thread
from flask import Flask, request, render_template, send_from_directory
from datetime import datetime

# Flask app initialization
app = Flask(__name__)

# Ports
HTTP_PORT = 3000
SOCKET_PORT = 5000


def save_data_to_json(user, message):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    new_data = {
        time_now: {
            'username': user,
            'message': message
        }
    }

    try:
        with open('storage/data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    data.update(new_data)

    with open('storage/data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/message', methods=['POST', 'GET'])
def message():
    if request.method == 'POST':
        username = request.form['username']
        message = request.form['message']
        # Send data via UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(f"{username}:{message}".encode(), ('localhost', SOCKET_PORT))
        save_data_to_json(username, message)
    return render_template('message.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


def run_flask():
    app.run(port=HTTP_PORT)


def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(('localhost', SOCKET_PORT))
        while True:
            data, _ = server.recvfrom(1024)
            message = data.decode()
            username, message_text = message.split(':', 1)
            save_data_to_json(username, message_text)


if __name__ == "__main__":
    # Create and start threads for Flask and Socket servers
    flask_thread = Thread(target=run_flask)
    socket_thread = Thread(target=run_socket_server)

    flask_thread.start()
    socket_thread.start()

    flask_thread.join()
    socket_thread.join()
