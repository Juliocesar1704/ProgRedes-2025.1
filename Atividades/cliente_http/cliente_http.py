import socket
import ssl

def extrairDados(url: str) -> tuple:
    if url.startswith("http://"):
        esquema = "http"
        url = url[len("http://"):]
    elif url.startswith("https://"):
        esquema = "https"
        url = url[len("https://"):]
    else:
        raise ValueError("URL inválida. Tente novamente com http:// ou https://")

    partes = url.split("/")
    host = partes[0]
    caminho = "/" + "/".join(partes[1:]) if len(partes) > 1 else "/"
    nome_arquivo = partes[-1] if "." in partes[-1] else ""

    return esquema, host, caminho, nome_arquivo

# Entrada do usuário
url = input("Digite a URL completa: ")
esquema, host, caminho, nome_arquivo = extrairDados(url)

# Resolve IP
try:
    ip_address = socket.gethostbyname(host)
except socket.gaierror as e:
    print(f"Erro ao resolver o host '{host}': {e}")
    exit(1)

# Exibe informações
print(f"\nEsquema.......: {esquema}")
print(f"Host..........: {host}")
print(f"Endereço IP...: {ip_address}")
print(f"Caminho.......: {caminho}")
print(f"Nome do arquivo: {nome_arquivo}")

# Define porta com base no protocolo
porta = 443 if esquema == "https" else 80
print(f"\nConectando a {host} na porta {porta}...")

# Cria e conecta o socket
sock = socket.create_connection((host, porta))
if esquema == "https":
    contexto = ssl.create_default_context()
    sock = contexto.wrap_socket(sock, server_hostname=host)

# Monta e envia a requisição GET
request = (
    f"GET {caminho} HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    f"User-Agent: PythonSocketClient/1.0\r\n"
    f"Connection: close\r\n\r\n"
)
sock.sendall(request.encode())

print("\nRequisição enviada. Aguardando resposta...")

# Lê a resposta completa
response = b""
while True:
    dados = sock.recv(4096)
    if not dados:
        break
    response += dados

sock.close()

# Divide a resposta em HEADER e BODY
separador = b"\r\n\r\n"
split_response = response.split(separador, 1)

header_bytes = split_response[0]
body_bytes = split_response[1] if len(split_response) > 1 else b""

# Salva o HEADER da resposta em um arquivo .txt
with open("header_resposta.txt", "w", encoding="utf-8") as f:
    f.write(header_bytes.decode(errors="replace"))

# Exibe prévia da resposta
print("\n===== Início da Resposta HTTP(S) =====")
print(header_bytes.decode(errors="replace"))
print("\n===== Fim do HEADER (salvo em header_resposta.txt) =====")



# Exemplos de URLs para testes:
"""
Arquivos de mídia:
Imagem: https://www.example.com/images/logo.png
Vídeo: https://www.example.com/videos/tutorial.mp4
Áudio: https://www.example.com/audio/song.mp3
"""

"""
Arquivos de texto:
Documento PDF: https://www.example.com/documents/report.pdf
Arquivo CSV: https://www.example.com/data/sales.csv
Arquivo JSON: https://www.example.com/api/data.json
"""
