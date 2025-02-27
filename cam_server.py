import socket
import threading
import xml.etree.ElementTree as ET
import re
import sys
import requests

# Definir o namespace do XML
NAMESPACE = {'ns': 'http://www.isapi.org/ver20/XMLSchema'}

def trigger_to_player():
    endpoint_player = 'http://192.168.15.20:9000/intervention'
    payload = 'carro=passou'

    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-token':'0987654321-hgfedcba'}
    r = requests.request('POST', endpoint_player, headers = headers, data = payload)
    print(r.headers)
    print(r.text)
    print(payload)

# Função para processar o XML recebido
def process_received_xml(data):
    try:
        # Limpeza básica - remove espaços em branco no início e no final da string
        data = data.strip()

        # Verificando se o dado começa com "<?xml" (indicativo de XML válido)
        if not data.startswith("<?xml"):
            print("Os dados recebidos não parecem ser XML válido.")
            return
        
        print(f"XML Recebido:\n{data}")

        root = ET.fromstring(data)
        
        event_notification = root.find('ns:EventNotificationAlert', NAMESPACE)
        if event_notification is not None:
            ip_address = event_notification.find('ns:ipAddress', NAMESPACE).text
            print(f"IP Address: {ip_address}")
            
            event_type = event_notification.find('ns:eventType', NAMESPACE).text
            print(f"Event Type: {event_type}")
            
            anpr = event_notification.find('ns:ANPR', NAMESPACE)
            if anpr is not None:
                license_plate = anpr.find('ns:licensePlate', NAMESPACE).text
                print(f"License Plate: {license_plate}")

                country = anpr.find('ns:country', NAMESPACE).text
                print(f"Country: {country}")

                picture_info = event_notification.find('ns:pictureInfoList/ns:pictureInfo', NAMESPACE)
                if picture_info is not None:
                    file_name = picture_info.find('ns:fileName', NAMESPACE).text
                    print(f"Picture File Name: {file_name}")

        else:
            print("EventNotificationAlert não encontrado no XML.")

    except ET.ParseError as e:
        print(f"Erro ao parsear o XML: {e}")

def handle_client_connection(client_socket, addr):
    try:
        print(f"Conexão estabelecida com {addr}")
        
        client_socket.settimeout(10)
        
        # Recebendo dados
        data = b""
        while True:
            chunk = client_socket.recv(1024)  # Lendo em pedaços de 1024 bytes
            if not chunk:
                break
            data += chunk  # Concatenando os pedaços recebidos
            #client_socket.send(b'player')

        if data:
            data_str = data.decode('utf-8', 'ignore')  # Ignora bytes inválidos
            print(f"Dados recebidos de {addr}: {data_str[:5000]}...")  # Exibe os primeiros 5000 caracteres dos dados recebidos
            trigger_to_player()
            # Identificar e remover cabeçalhos HTTP
            body = extract_body_from_multipart(data_str)
            if body:
                print(f"Corpo da requisição (XML esperado):\n{body[:500]}...")  # Exibe o início do corpo
                process_received_xml(body)  # Processa o XML recebido
            else:
                print("Não foi possível encontrar o corpo da requisição.")
        else:
            print(f"Conexão fechada por {addr} sem dados recebidos.")
        
        client_socket.close()
    except Exception as e:
        print(f"Erro na comunicação com o cliente {addr}: {e}")
        client_socket.close()

# Função para extrair o corpo do multipart/form-data
def extract_body_from_multipart(data):
    # Identificar a boundary no cabeçalho Content-Type
    boundary_match = re.search(r'boundary=([^\r\n]+)', data)
    if boundary_match:
        boundary = boundary_match.group(1)
        boundary = f'--{boundary}'
        
        # Encontrar o corpo após o cabeçalho
        body_match = re.search(rf'{re.escape(boundary)}\r\n\r\n(.*?){re.escape(boundary)}--', data, re.DOTALL)
        if body_match:
            body = body_match.group(1).strip()
            return body
    return None

def start_tcp_server():
    host = '192.168.15.3'
    port = 8844

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)


    print(f"Aguardando conexão em {host}:{port}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            # Usando threading para lidar com múltiplos clientes
            client_thread = threading.Thread(target=handle_client_connection, args=(client_socket, addr))
            client_thread.start()
        except Exception as e:
            print(f"Erro ao aceitar conexão: {e}")

start_tcp_server()
