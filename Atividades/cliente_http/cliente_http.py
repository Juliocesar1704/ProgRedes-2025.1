def extrairDados(url: str) -> tuple:
    # Extrai o esquema
    if url.startswith("http://"):
        esquema = "http"
        url = url[len("http://"):]
    elif url.startswith("https://"):
        esquema = "https"
        url = url[len("https://"):]
    else:
        esquema = "http"  # Padrão

    # Divide a URL em partes
    partes = url.split("/")
    host = partes[0]
    caminho = "/" + "/".join(partes[1:]) if len(partes) > 1 else ""
    
    # Nome do arquivo (último trecho após a última '/')
    if caminho and "." in partes[-1]:
        nome_arquivo = partes[-1]
    else:
        nome_arquivo = ""

    return esquema, host, caminho, nome_arquivo

# Entrada do usuário
url = input("Digite a URL completa: ")

# Processamento
esquema, host, caminho, nome_arquivo = extrairDados(url)

# Saída
print(f"Esquema.......: {esquema}")
print(f"Host..........: {host}")
print(f"Caminho.......: {caminho}")
print(f"Nome do arquivo: {nome_arquivo}")
