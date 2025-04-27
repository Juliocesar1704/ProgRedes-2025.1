import json
from tabulate import tabulate
from colorama import init, Fore, Style
import re

# Inicializa o colorama para que as cores sejam resetadas automaticamente após cada print
init(autoreset=True)

# Valida se o IP digitado está no formato correto (ex: 192.168.0.1)
def validar_ip(ip):
    partes = ip.split(".")  # Divide o IP em partes usando ponto como separador
    if len(partes) != 4:
        return False
    for parte in partes:
        if not parte.isdigit():
            return False
        num = int(parte)
        if num < 0 or num > 255:
            return False
    return True

# Converte um IP para um número inteiro (ex: 192.168.0.1 -> 3232235521)
def ip_para_inteiro(ip):
    partes = ip.split(".")
    return int(partes[0]) * 16777216 + int(partes[1]) * 65536 + int(partes[2]) * 256 + int(partes[3])

# Converte um número inteiro para um endereço IP (ex: 3232235521 -> 192.168.0.1)
def inteiro_para_ip(inteiro):
    octeto1 = inteiro // 16777216
    resto = inteiro % 16777216
    octeto2 = resto // 65536
    resto = resto % 65536
    octeto3 = resto // 256
    octeto4 = resto % 256
    return f"{octeto1}.{octeto2}.{octeto3}.{octeto4}"

# Gera uma máscara de sub-rede em formato binário com base no CIDR (ex: /24 -> 24 '1's e 8 '0's)
def mascara_para_binario(cidr):
    mascara = ""
    contador = 0
    while contador < cidr:
        mascara += "1"
        contador += 1
    while len(mascara) < 32:
        mascara += "0"
    return mascara

# Converte uma máscara binária para o formato decimal pontuado (ex: 11111111... -> 255.255.255.0)
def binario_para_decimal_pontuado(binario):
    octetos = []
    i = 0
    while i < 32:
        octeto = binario[i:i+8]
        decimal = int(octeto, 2)
        octetos.append(str(decimal))
        i += 8
    return ".".join(octetos)

# Calcula o número de hosts válidos com base no CIDR
def calcular_hosts_validos(cidr):
    if cidr == 31:
        return 2  # Exceção: /31 é usado para enlaces ponto-a-ponto
    if cidr == 32:
        return 0  # Exceção: /32 representa apenas um host (sem rede/broadcast)
    bits_host = 32 - cidr
    return (2 ** bits_host) - 2  # Total de endereços menos rede e broadcast

# Calcula o endereço de rede e de broadcast com base no IP e no CIDR
def calcular_rede_broadcast(ip_inteiro, cidr):
    total_ips = 2 ** (32 - cidr)  # Total de IPs na sub-rede
    endereco_rede = (ip_inteiro // total_ips) * total_ips  # Endereço base da sub-rede
    endereco_broadcast = endereco_rede + total_ips - 1  # Último IP da sub-rede
    return endereco_rede, endereco_broadcast

# Remove códigos de cores ANSI (útil se fosse preciso para versões sem cor)
def limpar_cores(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

# Função principal da calculadora de sub-redes
def calculadora_sub_rede():
    # Solicita o IP de entrada e valida
    endereco_ip = input("Digite o endereço IP: ")
    while not validar_ip(endereco_ip):
        print("IP inválido. Tente novamente.")
        endereco_ip = input("Digite o endereço IP: ")

    # Solicita o CIDR inicial
    while True:
        try:
            mascara_inicial = int(input("Digite a máscara de rede inicial (CIDR, entre 1 e 32): "))
            if mascara_inicial < 1 or mascara_inicial > 32:
                raise ValueError
            break
        except ValueError:
            print("Valor inválido. Digite um número entre 1 e 32.")

    # Solicita o CIDR final
    while True:
        try:
            mascara_final = int(input("Digite a máscara de rede final (CIDR, entre 1 e 32): "))
            if mascara_final < mascara_inicial or mascara_final > 32:
                raise ValueError
            break
        except ValueError:
            print(f"Valor inválido. Digite um número entre {mascara_inicial} e 32.")

    # Converte o IP para inteiro para facilitar cálculos
    ip_inteiro = ip_para_inteiro(endereco_ip)
    
    # Listas para guardar os resultados: terminal (com cor) e JSON (sem cor)
    resultados_para_terminal = []
    resultados_para_json = []

    cidr = mascara_inicial
    while cidr <= mascara_final:
        mascara_bin = mascara_para_binario(cidr)
        mascara_pontuada = binario_para_decimal_pontuado(mascara_bin)

        # Calcula os endereços de rede e broadcast
        endereco_rede, endereco_broadcast = calcular_rede_broadcast(ip_inteiro, cidr)

        # Define primeiro e último IP válidos (respeitando exceções para /31 e /32)
        if cidr == 31:
            primeiro_ip = endereco_rede
            ultimo_ip = endereco_broadcast
        elif cidr == 32:
            primeiro_ip = ultimo_ip = endereco_rede
        else:
            primeiro_ip = endereco_rede + 1
            ultimo_ip = endereco_broadcast - 1

        # Número de hosts válidos
        hosts_validos = calcular_hosts_validos(cidr)

        # Cria linha de resultado para o terminal (com cores)
        resultado_terminal = [
            f"/{cidr}",
            f"{Fore.BLUE}{inteiro_para_ip(endereco_rede)}",
            f"{Fore.GREEN}{inteiro_para_ip(primeiro_ip)}",
            f"{Fore.YELLOW}{inteiro_para_ip(ultimo_ip)}",
            f"{Fore.RED}{inteiro_para_ip(endereco_broadcast)}",
            f"{Fore.CYAN}{mascara_pontuada}",
            f"{Fore.MAGENTA}{mascara_bin[:8]}.{mascara_bin[8:16]}.{mascara_bin[16:24]}.{mascara_bin[24:]}"
        ]
        resultados_para_terminal.append(resultado_terminal)

        # Cria dicionário limpo para exportar no JSON
        resultado_json = {
            "CIDR": f"/{cidr}",
            "Endereco de Rede": inteiro_para_ip(endereco_rede),
            "Primeiro Host": inteiro_para_ip(primeiro_ip),
            "Ultimo Host": inteiro_para_ip(ultimo_ip),
            "Endereco de Broadcast": inteiro_para_ip(endereco_broadcast),
            "Mascara de Sub-Rede": mascara_pontuada,
            "Mascara de Sub-Rede (Binario)": f"{mascara_bin[:8]}.{mascara_bin[8:16]}.{mascara_bin[16:24]}.{mascara_bin[24:]}",
            "Hosts Validos": hosts_validos
        }
        resultados_para_json.append(resultado_json)

        # Cabeçalhos das tabelas
        headers = [
            f"{Fore.WHITE}Máscara",
            f"{Fore.WHITE}Endereço de Rede",
            f"{Fore.WHITE}Primeiro Host",
            f"{Fore.WHITE}Último Host",
            f"{Fore.WHITE}Endereço de Broadcast",
            f"{Fore.WHITE}Máscara de Sub-rede",
            f"{Fore.WHITE}Máscara de Sub-rede (Binário)"
        ]
        hosts_headers = [f"{Fore.WHITE}Hosts Válidos"]

        # Exibe o resultado da sub-rede no terminal com formatação
        print(f"\n{Style.BRIGHT}Sub-rede para máscara {cidr}: {Style.RESET_ALL}")
        print(tabulate([resultado_terminal], headers=headers, tablefmt="grid"))
        print(tabulate([[f"{Fore.MAGENTA}{hosts_validos}{Style.RESET_ALL}"]], headers=hosts_headers, tablefmt="grid"))

        cidr += 1

    # Salva os resultados em formato JSON sem cores
    with open("resultado_subredes.json", "w", encoding="utf-8") as arquivo_json:
        json.dump(resultados_para_json, arquivo_json, indent=4, ensure_ascii=False)

    print(f"\n{Fore.GREEN}Resultados salvos no arquivo 'resultado_subredes.json'.{Style.RESET_ALL}")

# Ponto de entrada do programa
if __name__ == "__main__":
    calculadora_sub_rede()
