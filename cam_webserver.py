import socket
import threading
import xml.etree.ElementTree as ET
import re
import sys
import requests
from flask import Flask, jsonify
from flask_socketio import SocketIO

# Configuração do Flask e WebSockets
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuração do servidor TCP
HOST = '192.168.15.3'
PORT = 8844

NAMESPACE = {'ns': 'http://www.isapi.org/ver20/XMLSchema'}

# Função que envia informações para o front-end
def send_to_frontend(data):
    socketio.emit('new_data', data)

def trigger_to_player():
    endpoint_player = 'http://192.168.15.20:9000/intervention'
    payload = 'carro=passou'

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-token': '0987654321-hgfedcba'}
    r = requests.request('POST', endpoint_player, headers=headers, data=payload)
    
    response_data = {
        "status_code": r.status_code,
        "headers": dict(r.headers),
        "text": r.text
    }
    
    send_to_frontend(response_data)
    print(response_data)

def process_received_xml(data):
    try:
        data = data.strip()
        if not data.startswith("<?xml"):
            print("Dados não são XML válido.")
            return
        
        print(f"XML Recebido:\n{data}")
        root = ET.fromstring(data)
        event_notification = root.find('ns:EventNotificationAlert', NAMESPACE)
        
        if event_notification is not None:
            ip_address = event_notification.find('ns:ipAddress', NAMESPACE).text
            event_type = event_notification.find('ns:eventType', NAMESPACE).text
            anpr = event_notification.find('ns:ANPR', NAMESPACE)

            extracted_data = {
                "ip_address": ip_address,
                "event_type": event_type,
                "license_plate": anpr.find('ns:licensePlate', NAMESPACE).text if anpr else None,
                "country": anpr.find('ns:country', NAMESPACE).text if anpr else None,
            }
            
            send_to_frontend(extracted_data)
            print(extracted_data)
        else:
            print("EventNotificationAlert não encontrado.")
    
    except ET.ParseError as e:
        print(f"Erro ao processar XML: {e}")

def handle_client_connection(client_socket, addr):
    try:
        print(f"Conexão com {addr}")
        client_socket.settimeout(10)
        
        data = b""
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            data += chunk

        if data:
            data_str = data.decode('utf-8', 'ignore')
            print(f"Recebido de {addr}: {data_str[:5000]}...")
            trigger_to_player()

            body = extract_body_from_multipart(data_str)
            if body:
                print(f"Corpo da requisição:\n{body[:500]}...")
                process_received_xml(body)
            else:
                print("Corpo da requisição não encontrado.")
        else:
            print(f"Conexão fechada por {addr} sem dados.")

        client_socket.close()

    except Exception as e:
        print(f"Erro na comunicação com {addr}: {e}")
        client_socket.close()

def extract_body_from_multipart(data):
    boundary_match = re.search(r'boundary=([^\r\n]+)', data)
    if boundary_match:
        boundary = f'--{boundary_match.group(1)}'
        body_match = re.search(rf'{re.escape(boundary)}\r\n\r\n(.*?){re.escape(boundary)}--', data, re.DOTALL)
        if body_match:
            return body_match.group(1).strip()
    return None

def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Servidor TCP rodando em {HOST}:{PORT}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=handle_client_connection, args=(client_socket, addr)).start()
        except Exception as e:
            print(f"Erro ao aceitar conexão: {e}")

# Rota HTTP para verificar se o servidor está rodando
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "Servidor rodando!"})

if __name__ == '__main__':
    threading.Thread(target=start_tcp_server).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
