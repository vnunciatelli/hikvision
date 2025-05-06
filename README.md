# 🚗 Detecção de Veículos Acima do Limite de Velocidade com Câmera Hikvision

Este projeto implementa um sistema de monitoramento em tempo real que utiliza uma câmera Hikvision com protocolo ISAPI para detectar eventos de passagem de veículos. Ao receber eventos (por exemplo, passagem de carro detectada por radar), o sistema interpreta os dados XML recebidos, extrai informações relevantes como placa e país, e aciona um player externo ou envia os dados para um frontend em tempo real via WebSocket.

## 📦 Tecnologias Utilizadas

- **Python 3**
- **Flask** – Web framework para a API
- **Flask-SocketIO** – Comunicação em tempo real com o frontend
- **Socket TCP** – Para escutar eventos da câmera
- **XML Parsing (ElementTree)** – Para processar os dados do ISAPI
- **requests** – Para acionar o player externo via HTTP POST

## 🧠 Funcionamento Geral

1. A câmera Hikvision envia um pacote TCP com conteúdo XML no padrão ISAPI.
2. O servidor TCP embutido no código recebe os dados.
3. A estrutura XML é extraída da mensagem multipart e processada.
4. O sistema:
   - Extrai IP, tipo de evento, placa e país.
   - Aciona um player externo (por exemplo, painel, sirene, aviso visual) via HTTP POST.
   - Envia os dados para o frontend em tempo real via WebSocket.

## 📂 Estrutura dos Componentes

- `start_tcp_server`: Inicia o servidor TCP escutando a porta 8844.
- `handle_client_connection`: Trata conexões individuais e extrai XML válido.
- `process_received_xml`: Faz parsing do XML, extrai dados e envia ao frontend.
- `trigger_to_player`: Aciona um endpoint HTTP com os dados do evento.
- `send_to_frontend`: Usa WebSocket para transmitir dados ao navegador.

## 🖥️ Requisitos

- Python 3.8+
- Acesso a uma câmera Hikvision configurada para enviar eventos ISAPI via TCP
- Rede local com as permissões adequadas
