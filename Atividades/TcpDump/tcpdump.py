# Importando bibliotecas necessárias
import tkinter as tk
from tkinter import filedialog
from tabulate import tabulate
from colorama import Fore, Style, init

# Inicializando o colorama para suportar cores no terminal e configurando o estilo de reset automático
init(autoreset=True)

# abrindo uma janela para o usuário selecionar um arquivo .cap
def abrir_janela_selecao_arquivo():
    janela = tk.Tk()
    janela.withdraw()
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo PCAP",
        filetypes=[("Arquivos PCAP", "*.cap *.dump *.pcap"), ("Todos os arquivos", "*.*")]
    )
    return caminho_arquivo

# Função para ler um inteiro de 4 bytes em ordem little endian
def ler_inteiro_32bits_little_endian(blocos_bytes):
    return int.from_bytes(blocos_bytes, byteorder='little')

# Função para ler o cabeçalho de um arquivo PCAP e retornar uma lista de pacotes
def carregar_pacotes_pcap(caminho_arquivo):
    lista_pacotes = []

    with open(caminho_arquivo, 'rb') as arquivo:
        cabecalho_global = arquivo.read(24)
        if len(cabecalho_global) < 24:
            raise Exception("Cabeçalho global incompleto.")

        numero_magico = ler_inteiro_32bits_little_endian(cabecalho_global[0:4])
        versao_maior = int.from_bytes(cabecalho_global[4:6], 'little')
        versao_menor = int.from_bytes(cabecalho_global[6:8], 'little')
        snaplen = ler_inteiro_32bits_little_endian(cabecalho_global[16:20])
        tipo_link = ler_inteiro_32bits_little_endian(cabecalho_global[20:24])

        print(Fore.GREEN + "[INFO] Cabeçalho Global Lido:")
        dados_cabecalho = [
            ["Magic Number", hex(numero_magico)],
            ["Versão", f"{versao_maior}.{versao_menor}"],
            ["SnapLen", snaplen],
            ["LinkType", tipo_link]
        ]
        print(tabulate(dados_cabecalho, headers=["Campo", "Valor"], tablefmt="fancy_grid"))

        while True:
            cabecalho_pacote = arquivo.read(16)
            if len(cabecalho_pacote) < 16:
                break  # Fim do arquivo

            timestamp_segundos = ler_inteiro_32bits_little_endian(cabecalho_pacote[0:4])
            timestamp_micros = ler_inteiro_32bits_little_endian(cabecalho_pacote[4:8])
            comprimento_capturado = ler_inteiro_32bits_little_endian(cabecalho_pacote[8:12])
            comprimento_original = ler_inteiro_32bits_little_endian(cabecalho_pacote[12:16])

            conteudo_pacote = arquivo.read(comprimento_capturado)
            if len(conteudo_pacote) < comprimento_capturado:
                break  # Arquivo truncado

            pacote = {
                'timestamp': timestamp_segundos + timestamp_micros / 1_000_000,
                'caplen': comprimento_capturado,
                'origlen': comprimento_original,
                'dados': conteudo_pacote
            }
            lista_pacotes.append(pacote)

    print(Fore.BLUE + f"\n[INFO] {len(lista_pacotes)} pacotes foram carregados com sucesso.")
    return lista_pacotes

# Função para exibir os cabeçalhos IP dos pacotes
def exibir_headers_ip(lista_pacotes):
    print(Fore.YELLOW + "\n[INFO] Analisando cabeçalhos IP dos pacotes...")

    tabelas = []
    contador = 0

    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue  

        # Ignorar cabeçalho Ethernet (primeiros 14 bytes)
        cabecalho_ip = dados[14:34]

        # Extrair versão e IHL
        byte_0 = cabecalho_ip[0]
        versao_ip = byte_0 >> 4
        tamanho_cabecalho = (byte_0 & 0x0F) * 4

        # Tamanho total do datagrama
        tamanho_total = int.from_bytes(cabecalho_ip[2:4], byteorder='big')

        identificacao = int.from_bytes(cabecalho_ip[4:6], byteorder='big')

        flags_fragmento = int.from_bytes(cabecalho_ip[6:8], byteorder='big')
        flags = flags_fragmento >> 13
        fragment_offset = flags_fragmento & 0x1FFF

        ttl = cabecalho_ip[8]
        protocolo = cabecalho_ip[9]

        ip_origem = ".".join(str(b) for b in cabecalho_ip[12:16])
        ip_destino = ".".join(str(b) for b in cabecalho_ip[16:20])

        contador += 1
        tabelas.append([
            contador,
            versao_ip,
            tamanho_cabecalho,
            tamanho_total,
            identificacao,
            flags,
            fragment_offset,
            ttl,
            protocolo,
            ip_origem,
            ip_destino
        ])

    print(tabulate(tabelas, headers=[
        "Pacote", "Versão", "IHL", "Tam. Total", "ID",
        "Flags", "Offset", "TTL", "Protocolo", "Origem", "Destino"
    ], tablefmt="fancy_grid"))

# Função para exibir o intervalo de captura de pacotes
def exibir_intervalo_captura(lista_pacotes):
    if not lista_pacotes:
        print(Fore.RED + "[ERRO] Nenhum pacote disponível para análise de tempo.")
        return

    lista_timestamps = []
    for pacote in lista_pacotes:
        lista_timestamps.append(pacote['timestamp'])

    tempo_inicio = min(lista_timestamps)
    tempo_fim = max(lista_timestamps)
    duracao = tempo_fim - tempo_inicio

    print(Fore.MAGENTA + "\n[INFO] Intervalo de captura de pacotes:")
    print(tabulate([
        ["Início da captura (segundos)", f"{tempo_inicio:.6f}"],
        ["Fim da captura (segundos)", f"{tempo_fim:.6f}"],
        ["Duração total (segundos)", f"{duracao:.6f}"]
    ], headers=["Descrição", "Valor"], tablefmt="fancy_grid"))

# Função principal para executar o código
if __name__ == "__main__":
    caminho_selecionado = abrir_janela_selecao_arquivo()
    
    if caminho_selecionado:
        pacotes_lidos = carregar_pacotes_pcap(caminho_selecionado)
        exibir_headers_ip(pacotes_lidos)
        exibir_intervalo_captura(pacotes_lidos)
    else:
        print(Fore.RED + "[ERRO] Nenhum arquivo foi selecionado.")
