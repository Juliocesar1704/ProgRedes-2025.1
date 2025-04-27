from funcoes import findNonce
from fpdf import FPDF

# Lista de testes
testes = [
    ("Esse é fácil", 8),
    ("Esse é fácil", 10),
    ("Esse é fácil", 15),
    ("Texto maior muda o tempo?", 8),
    ("Texto maior muda o tempo?", 10),
    ("Texto maior muda o tempo?", 15),
    ("É possível calcular esse?", 18),
    ("É possível calcular esse?", 19),
    ("É possível calcular esse?", 20),
]

# Executa os testes e salva os resultados
resultados = []
for texto, bits in testes:
    data_bytes = texto.encode('utf-8')
    nonce, tempo = findNonce(data_bytes, bits)
    resultados.append((texto, bits, nonce, round(tempo, 2)))

# Cria um objeto PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

# Adiciona um título
pdf.cell(0, 10, "Resultados dos Testes - findNonce", ln=True, align="C")
pdf.ln(10)

# Adiciona o cabeçalho da tabela
pdf.set_font("Arial", "B", 12)
pdf.cell(60, 10, "Texto", 1)
pdf.cell(30, 10, "Bits Zero", 1)
pdf.cell(50, 10, "Nonce", 1)
pdf.cell(30, 10, "Tempo (s)", 1)
pdf.ln()

# Adiciona os dados
pdf.set_font("Arial", size=12)
for texto, bits, nonce, tempo in resultados:
    pdf.cell(60, 10, texto[:25], 1)  # Limita o tamanho para caber na célula
    pdf.cell(30, 10, str(bits), 1)
    pdf.cell(50, 10, str(nonce), 1)
    pdf.cell(30, 10, str(tempo), 1)
    pdf.ln()

# Nome do arquivo PDF
arquivo_pdf = "tabela_resultados.pdf"
pdf.output(arquivo_pdf)

# Mensagem final
print(f"\n[✅] Resultados salvos no arquivo PDF: {arquivo_pdf}\n")
