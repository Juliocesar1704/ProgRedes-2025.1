import tkinter as tk
from tkinter import filedialog
import json
import csv
from fpdf import FPDF

# Função para abrir a janela de seleção de arquivo PCAP
def abrir_janela_selecao_arquivo():
    janela = tk.Tk()
    janela.withdraw()  # Esconde a janela principal do Tkinter
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo para a analise",
        filetypes=[("Arquivos PCAP", "*.cap *.dump *.pcap"), ("Todos os arquivos", "*.*")]
    )
    return caminho_arquivo

# Função para ler um inteiro de 4 bytes em ordem little endian
def ler_inteiro_32bits_little_endian(blocos_bytes):
    return int.from_bytes(blocos_bytes, byteorder='little')

# Função para carregar os pacotes de um arquivo PCAP
def carregar_pacotes_pcap(caminho_arquivo):
    lista_pacotes = []

    with open(caminho_arquivo, 'rb') as arquivo:
        # Lê o cabeçalho global do arquivo PCAP (24 bytes)
        cabecalho_global = arquivo.read(24)
        if len(cabecalho_global) < 24:
            raise Exception("Cabeçalho global incompleto.")

        # Extrai informações do cabeçalho global
        numero_magico = ler_inteiro_32bits_little_endian(cabecalho_global[0:4])
        versao_maior = int.from_bytes(cabecalho_global[4:6], 'little')
        versao_menor = int.from_bytes(cabecalho_global[6:8], 'little')
        snaplen = ler_inteiro_32bits_little_endian(cabecalho_global[16:20])
        tipo_link = ler_inteiro_32bits_little_endian(cabecalho_global[20:24])

        # Exibe informações básicas do cabeçalho global
        print("[INFO] Cabeçalho Global Lido:")
        print(f"Magic Number: {hex(numero_magico)}")
        print(f"Versão: {versao_maior}.{versao_menor}")
        print(f"SnapLen: {snaplen}")
        print(f"LinkType: {tipo_link}")

        # Loop para ler cada pacote no arquivo
        while True:
            cabecalho_pacote = arquivo.read(16)  # Cabeçalho de cada pacote (16 bytes)
            if len(cabecalho_pacote) < 16:
                break  # Fim do arquivo

            # Extrai timestamps e comprimentos do pacote
            timestamp_segundos = ler_inteiro_32bits_little_endian(cabecalho_pacote[0:4])
            timestamp_micros = ler_inteiro_32bits_little_endian(cabecalho_pacote[4:8])
            comprimento_capturado = ler_inteiro_32bits_little_endian(cabecalho_pacote[8:12])
            comprimento_original = ler_inteiro_32bits_little_endian(cabecalho_pacote[12:16])

            # Lê os dados do pacote (payload)
            conteudo_pacote = arquivo.read(comprimento_capturado)
            if len(conteudo_pacote) < comprimento_capturado:
                break  # Arquivo truncado, pacote incompleto

            # Armazena os dados do pacote numa estrutura dicionário
            pacote = {
                'timestamp': timestamp_segundos + timestamp_micros / 1_000_000,
                'caplen': comprimento_capturado,
                'origlen': comprimento_original,
                'dados': conteudo_pacote
            }
            lista_pacotes.append(pacote)

    print(f"\n[INFO] {len(lista_pacotes)} pacotes foram carregados com sucesso.")
    return lista_pacotes

# Função para extrair e organizar os cabeçalhos IP dos pacotes em uma tabela
def obter_headers_ip(lista_pacotes):
    tabelas = []
    contador = 0
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue  # Pacote muito pequeno para conter cabeçalho IP
        cabecalho_ip = dados[14:34]  # Ignora cabeçalho Ethernet (14 bytes)
        byte_0 = cabecalho_ip[0]
        versao_ip = byte_0 >> 4  # Versão IP (4 bits mais significativos)
        tamanho_cabecalho = (byte_0 & 0x0F) * 4  # IHL (número de palavras de 32 bits * 4 = bytes)
        tamanho_total = int.from_bytes(cabecalho_ip[2:4], byteorder='big')
        identificacao = int.from_bytes(cabecalho_ip[4:6], byteorder='big')
        flags_fragmento = int.from_bytes(cabecalho_ip[6:8], byteorder='big')
        flags = flags_fragmento >> 13  # 3 bits de flags
        fragment_offset = flags_fragmento & 0x1FFF  # 13 bits de offset
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
    return ("Cabeçalhos IP dos pacotes", [["Pacote", "Versão", "IHL", "Tam. Total", "ID",
                                          "Flags", "Offset", "TTL", "Protocolo", "Origem", "Destino"]] + tabelas)

# Função para calcular o intervalo de captura dos pacotes
def obter_intervalo_captura(lista_pacotes):
    if not lista_pacotes:
        return ("Intervalo de captura de pacotes", [["Erro"], ["Nenhum pacote disponível para análise"]])
    lista_timestamps = [p['timestamp'] for p in lista_pacotes]
    tempo_inicio = min(lista_timestamps)
    tempo_fim = max(lista_timestamps)
    duracao = tempo_fim - tempo_inicio
    tabela = [
        ["Descrição", "Valor"],
        ["Início da captura (segundos)", f"{tempo_inicio:.6f}"],
        ["Fim da captura (segundos)", f"{tempo_fim:.6f}"],
        ["Duração total (segundos)", f"{duracao:.6f}"]
    ]
    return ("Intervalo de captura de pacotes", tabela)

# Função para identificar o maior pacote TCP capturado
def obter_maior_pacote_tcp(lista_pacotes):
    maior_tamanho_tcp = 0
    ip_origem_maior = ""
    ip_destino_maior = ""
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue
        cabecalho_ip = dados[14:34]
        protocolo = cabecalho_ip[9]
        if protocolo != 6:  # Apenas TCP
            continue
        tamanho_original = pacote['origlen']
        if tamanho_original > maior_tamanho_tcp:
            maior_tamanho_tcp = tamanho_original
            ip_origem_maior = ".".join(str(b) for b in cabecalho_ip[12:16])
            ip_destino_maior = ".".join(str(b) for b in cabecalho_ip[16:20])
    tabela = [
        ["Campo", "Valor"],
        ["Tamanho (bytes)", maior_tamanho_tcp],
        ["IP de Origem", ip_origem_maior],
        ["IP de Destino", ip_destino_maior]
    ]
    return ("Maior pacote TCP capturado", tabela)

# Função para contar pacotes truncados
def obter_pacotes_truncados(lista_pacotes):
    truncados = 0
    for pacote in lista_pacotes:
        if pacote['caplen'] < pacote['origlen']:
            truncados += 1
    tabela = [
        ["Descrição", "Valor"],
        ["Total de pacotes analisados", len(lista_pacotes)],
        ["Pacotes truncados (caplen < origlen)", truncados]
    ]
    return ("Verificação de pacotes truncados", tabela)

# Função para calcular o tamanho médio dos pacotes UDP
def obter_tamanho_medio_udp(lista_pacotes):
    soma_tamanhos_udp = 0
    quantidade_udp = 0
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue
        cabecalho_ip = dados[14:34]
        protocolo = cabecalho_ip[9]
        if protocolo == 17:  # UDP
            soma_tamanhos_udp += pacote['origlen']
            quantidade_udp += 1
    if quantidade_udp == 0:
        return ("Tamanho médio dos pacotes UDP capturados", [["Info"], ["Nenhum pacote UDP foi encontrado."]])
    media = soma_tamanhos_udp / quantidade_udp
    tabela = [
        ["Descrição", "Valor"],
        ["Total de pacotes UDP", quantidade_udp],
        ["Tamanho médio (bytes)", f"{media:.2f}"]
    ]
    return ("Tamanho médio dos pacotes UDP capturados", tabela)

# Função para identificar o par de IPs com maior tráfego
def obter_maior_trafego_por_par(lista_pacotes):
    trafego_por_par = {}
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue
        cabecalho_ip = dados[14:34]
        ip_origem = ".".join(str(b) for b in cabecalho_ip[12:16])
        ip_destino = ".".join(str(b) for b in cabecalho_ip[16:20])
        par = (ip_origem, ip_destino)
        if par not in trafego_por_par:
            trafego_por_par[par] = 0
        trafego_por_par[par] += pacote['origlen']
    if not trafego_por_par:
        return ("Par de IPs com maior tráfego", [["Info"], ["Nenhum par de IPs encontrado."]])
    par_mais_trafego = max(trafego_por_par, key=trafego_por_par.get)
    total_bytes = trafego_por_par[par_mais_trafego]
    tabela = [
        ["Campo", "Valor"],
        ["IP de Origem", par_mais_trafego[0]],
        ["IP de Destino", par_mais_trafego[1]],
        ["Total de Dados (bytes)", total_bytes]
    ]
    return ("Par de IPs com maior tráfego", tabela)

# Função para identificar interações da interface local (IP mais frequente)
def obter_interacoes_da_interface(lista_pacotes):
    contagem_origem = {}
    interacoes = set()
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue
        cabecalho_ip = dados[14:34]
        ip_origem = ".".join(str(b) for b in cabecalho_ip[12:16])
        ip_destino = ".".join(str(b) for b in cabecalho_ip[16:20])
        if ip_origem not in contagem_origem:
            contagem_origem[ip_origem] = 0
        contagem_origem[ip_origem] += 1
    if not contagem_origem:
        return ("Interações da interface local", [["Erro"], ["Nenhum IP encontrado para análise."]])
    ip_interface = max(contagem_origem, key=contagem_origem.get)
    for pacote in lista_pacotes:
        dados = pacote['dados']
        if len(dados) < 34:
            continue
        cabecalho_ip = dados[14:34]
        ip_origem = ".".join(str(b) for b in cabecalho_ip[12:16])
        ip_destino = ".".join(str(b) for b in cabecalho_ip[16:20])
        if ip_origem == ip_interface:
            interacoes.add(ip_destino)
        elif ip_destino == ip_interface:
            interacoes.add(ip_origem)
    tabela = [
        ["Campo", "Valor"],
        ["IP da Interface", ip_interface],
        ["Total de IPs diferentes que interagiram com ele", len(interacoes)]
    ]
    return ("Interações da interface local", tabela)

# Função para gerar nome fixo de arquivo de saída
def gerar_nome_arquivo(extensao):
    return f"relatorio_pcap.{extensao}"

# Exporta os dados para JSON
def exportar_para_json(tabelas):
    nome_arquivo = gerar_nome_arquivo("json")
    dados_json = {}
    for titulo, tabela in tabelas:
        dados_json[titulo] = [tabela[0]] + tabela[1:]
    with open(nome_arquivo, "w", encoding="utf-8") as f:  # Adicionado encoding utf-8
        json.dump(dados_json, f, indent=4, ensure_ascii=False)  # ensure_ascii=False para acentuação legível
    print(f"[OK] Dados exportados para {nome_arquivo}")

# Exporta os dados para CSV
def exportar_para_csv(tabelas):
    nome_arquivo = gerar_nome_arquivo("csv")
    with open(nome_arquivo, "w", newline="", encoding="utf-8") as csvfile:  # Adicionado encoding utf-8
        writer = csv.writer(csvfile)
        for titulo, tabela in tabelas:
            writer.writerow([titulo])
            writer.writerow(tabela[0])
            for linha in tabela[1:]:
                writer.writerow(linha)
            writer.writerow([])
    print(f"[OK] Dados exportados para {nome_arquivo}")

# Exporta os dados para PDF
def exportar_para_pdf(tabelas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for titulo, tabela in tabelas:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt=titulo, ln=True)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, txt=" | ".join(tabela[0]), ln=True)
        pdf.set_font("Arial", size=10)
        for linha in tabela[1:]:
            pdf.cell(0, 10, txt=" | ".join(str(item) for item in linha), ln=True)
        pdf.ln(5)
    nome_arquivo = gerar_nome_arquivo("pdf")
    pdf.output(nome_arquivo)
    print(f"[OK] Dados exportados para {nome_arquivo}")

# Função para solicitar o formato de saída ao usuário
def solicitar_formato_saida():
    print("\nEscolha o formato de exportação dos resultados:")
    print("1 - PDF")
    print("2 - JSON")
    print("3 - CSV")
    while True:
        escolha = input("Digite 1, 2 ou 3: ").strip()
        if escolha in ["1", "2", "3"]:
            return escolha
        print("Opção inválida. Tente novamente.")

# Bloco principal da execução do programa
if __name__ == "__main__":
    caminho_selecionado = abrir_janela_selecao_arquivo()

    if caminho_selecionado:
        pacotes_lidos = carregar_pacotes_pcap(caminho_selecionado)

        # Coleta os resultados das análises
        resultados = []
        resultados.append(obter_headers_ip(pacotes_lidos))
        resultados.append(obter_intervalo_captura(pacotes_lidos))
        resultados.append(obter_maior_pacote_tcp(pacotes_lidos))
        resultados.append(obter_pacotes_truncados(pacotes_lidos))
        resultados.append(obter_tamanho_medio_udp(pacotes_lidos))
        resultados.append(obter_maior_trafego_por_par(pacotes_lidos))
        resultados.append(obter_interacoes_da_interface(pacotes_lidos))

        # Solicita formato de saída e exporta
        formato = solicitar_formato_saida()
        if formato == "1":
            exportar_para_pdf(resultados)
        elif formato == "2":
            exportar_para_json(resultados)
        else:
            exportar_para_csv(resultados)
    else:
        print("[ERRO] Nenhum arquivo foi selecionado.")
