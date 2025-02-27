#include <iostream>
#include <thread>
#include <regex>
#include <string>
#include <asio.hpp>
#include <curl/curl.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

using asio::ip::tcp;

const std::string NAMESPACE = "http://www.isapi.org/ver20/XMLSchema";

// Função para enviar requisição HTTP
void trigger_to_player() {
    std::string endpoint_player = "http://192.168.15.20:9000/intervention";
    std::string payload = "carro=passou";
    std::string headers = "Content-Type: application/x-www-form-urlencoded\r\nx-token: 0987654321-hgfedcba\r\n";

    CURL *curl;
    CURLcode res;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, endpoint_player.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, curl_slist_append(nullptr, headers.c_str()));
        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "Erro na requisição: " << curl_easy_strerror(res) << std::endl;
        }
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
}

// Função para processar o XML
void process_received_xml(const std::string& data) {
    try {
        xmlDocPtr doc = xmlReadMemory(data.c_str(), data.size(), "noname.xml", NULL, 0);
        if (doc == nullptr) {
            std::cerr << "Erro ao parsear o XML" << std::endl;
            return;
        }

        xmlNodePtr root = xmlDocGetRootElement(doc);
        if (root == nullptr) {
            std::cerr << "O XML está vazio" << std::endl;
            xmlFreeDoc(doc);
            return;
        }

        xmlNodePtr event_notification = nullptr;
        for (xmlNodePtr node = root->children; node; node = node->next) {
            if (node->type == XML_ELEMENT_NODE && std::string((char*)node->name) == "EventNotificationAlert") {
                event_notification = node;
                break;
            }
        }

        if (event_notification != nullptr) {
            // Exemplo de como acessar elementos no XML
            xmlNodePtr ip_address_node = nullptr;
            for (xmlNodePtr node = event_notification->children; node; node = node->next) {
                if (node->type == XML_ELEMENT_NODE && std::string((char*)node->name) == "ipAddress") {
                    ip_address_node = node;
                    break;
                }
            }

            if (ip_address_node) {
                std::cout << "IP Address: " << (char*)xmlNodeGetContent(ip_address_node) << std::endl;
            }

            // Aqui você pode continuar para o evento e outros elementos
        }

        xmlFreeDoc(doc);
    } catch (const std::exception& e) {
        std::cerr << "Erro ao processar XML: " << e.what() << std::endl;
    }
}

// Função para lidar com a conexão do cliente
void handle_client_connection(tcp::socket& socket) {
    try {
        asio::streambuf buffer;
        asio::read_until(socket, buffer, "\r\n\r\n");  // Lê até o cabeçalho HTTP

        std::istream input_stream(&buffer);
        std::string data((std::istreambuf_iterator<char>(input_stream)), std::istreambuf_iterator<char>());

        std::cout << "Dados recebidos:\n" << data.substr(0, 5000) << "..." << std::endl;

        trigger_to_player();

        // Processar o XML
        std::string body = extract_body_from_multipart(data);
        if (!body.empty()) {
            std::cout << "Corpo da requisição (XML esperado):\n" << body.substr(0, 500) << "..." << std::endl;
            process_received_xml(body);
        } else {
            std::cerr << "Não foi possível encontrar o corpo da requisição." << std::endl;
        }

    } catch (std::exception& e) {
        std::cerr << "Erro na comunicação com o cliente: " << e.what() << std::endl;
    }
}

// Função para extrair o corpo do multipart/form-data
std::string extract_body_from_multipart(const std::string& data) {
    std::regex boundary_pattern("boundary=([^\r\n]+)");
    std::smatch match;
    if (std::regex_search(data, match, boundary_pattern)) {
        std::string boundary = "--" + match[1].str();
        std::regex body_pattern(boundary + "\r\n\r\n(.*?)" + boundary + "--", std::regex::dotall);
        if (std::regex_search(data, match, body_pattern)) {
            return match[1].str();
        }
    }
    return "";
}

// Função para iniciar o servidor TCP
void start_tcp_server() {
    try {
        asio::io_context io_context;
        tcp::acceptor acceptor(io_context, tcp::endpoint(tcp::v4(), 8844));

        std::cout << "Aguardando conexão em 192.168.15.3:8844" << std::endl;

        while (true) {
            tcp::socket socket(io_context);
            acceptor.accept(socket);
            std::thread(handle_client_connection, std::ref(socket)).detach();
        }
    } catch (const std::exception& e) {
        std::cerr << "Erro ao iniciar o servidor TCP: " << e.what() << std::endl;
    }
}

int main() {
    start_tcp_server();
    return 0;
}
