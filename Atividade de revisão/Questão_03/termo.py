import tkinter as tk
from tkinter import messagebox
import random

# Função para carregar as palavras de um arquivo .txt
def carregar_palavras():
    try:
        with open("palavras.txt", "r", encoding="utf-8") as arquivo:
            # Filtra apenas palavras com exatamente 5 letras, remove espaços e converte para maiúsculas
            return [linha.strip().upper() for linha in arquivo if len(linha.strip()) == 5]
    except FileNotFoundError:
        # Exibe erro se o arquivo não for encontrado
        messagebox.showerror("Erro", "O arquivo 'palavras.txt' não foi encontrado.")
        return []
    except Exception as e:
        # Exibe erro genérico se acontecer outro problema
        messagebox.showerror("Erro", f"Ocorreu um erro ao carregar o arquivo: {e}")
        return []

# Função que compara a tentativa com a palavra sorteada e gera feedback por letra
def verificar_feedback(palavra, tentativa):
    feedback = []
    for i, letra in enumerate(tentativa):
        if letra == palavra[i]:
            feedback.append(('g', letra))  # Letra certa e na posição certa (verde)
        elif letra in palavra:
            feedback.append(('y', letra))  # Letra certa mas na posição errada (amarelo)
        else:
            feedback.append(('b', letra))  # Letra errada (cinza)
    return feedback

# Remove todos os feedbacks anteriores do quadro
def limpar_feedback(frame, canvas):
    for widget in frame.winfo_children():
        widget.destroy()
    canvas.yview_moveto(0)  # Rola para o topo do canvas

# Exibe na interface o feedback de cada tentativa
def mostrar_feedback(frame, canvas, feedback):
    linha = tk.Frame(frame)
    linha.pack(pady=2)  # Espaçamento vertical entre as linhas

    for tipo, letra in feedback:
        cor = {"g": "green", "y": "yellow", "b": "gray"}[tipo]
        etiqueta = tk.Label(linha, text=letra, bg=cor, width=4, height=2, font=("Arial", 20))
        etiqueta.pack(side=tk.LEFT, padx=2)

    # Scroll automático para a parte inferior após mostrar feedback
    canvas.after(100, lambda: canvas.yview_moveto(1.0))

# Reinicia o jogo escolhendo uma nova palavra e resetando tentativas
def iniciar_jogo(estado, palavras, label_tentativas, frame_feedback, canvas_feedback):
    estado["palavra"] = random.choice(palavras)  # Nova palavra sorteada
    estado["tentativas"] = 6  # Reinicia o número de tentativas
    label_tentativas.config(text="Tentativas restantes: 6")
    limpar_feedback(frame_feedback, canvas_feedback)

# Lógica executada quando o usuário faz uma tentativa
def fazer_tentativa(entry, estado, label_tentativas, frame_feedback, canvas_feedback):
    tentativa = entry.get().upper().strip()  # Pega o texto da entrada e padroniza
    entry.delete(0, tk.END)  # Limpa o campo de entrada

    if len(tentativa) != len(estado["palavra"]):
        messagebox.showwarning("Erro", f"A palavra deve ter exatamente {len(estado['palavra'])} letras.")
        return

    feedback = verificar_feedback(estado["palavra"], tentativa)
    mostrar_feedback(frame_feedback, canvas_feedback, feedback)

    if tentativa == estado["palavra"]:
        messagebox.showinfo("Vitória!", f"Parabéns! Você acertou, a palvra era  : {estado['palavra']}")
        iniciar_jogo(estado, estado["palavras"], label_tentativas, frame_feedback, canvas_feedback)
        return

    estado["tentativas"] -= 1
    label_tentativas.config(text=f"Tentativas restantes: {estado['tentativas']}")

    if estado["tentativas"] == 0:
        messagebox.showinfo("Derrota", f"Você perdeu! A palavra era: {estado['palavra']}")
        iniciar_jogo(estado, estado["palavras"], label_tentativas, frame_feedback, canvas_feedback)

# Função principal para montar e rodar a interface gráfica
def main():
    root = tk.Tk()
    root.title("Jogo de Adivinhação de Palavras")
    root.geometry("520x600")  # Tamanho da janela

    palavras = carregar_palavras()
    if not palavras:
        root.quit()
        return

    # Dicionário que guarda o estado atual do jogo
    estado = {"palavra": "", "tentativas": 6, "palavras": palavras}

    # Cria o campo de entrada e botão de tentativa
    quadro_entrada = tk.Frame(root)
    quadro_entrada.pack(pady=10)

    campo_tentativa = tk.Entry(quadro_entrada, font=("Arial", 18), width=10)
    campo_tentativa.pack(side=tk.LEFT, padx=10)

    botao_tentativa = tk.Button(
        quadro_entrada, text="Tentar", font=("Arial", 18),
        command=lambda: fazer_tentativa(campo_tentativa, estado, label_tentativas, quadro_feedback, canvas_feedback)
    )
    botao_tentativa.pack(side=tk.LEFT)

    # Permite usar a tecla ENTER para enviar a tentativa
    campo_tentativa.bind("<Return>", lambda e: fazer_tentativa(campo_tentativa, estado, label_tentativas, quadro_feedback, canvas_feedback))

    # Label de tentativas restantes
    label_tentativas = tk.Label(root, text="Tentativas restantes: 6", font=("Arial", 18))
    label_tentativas.pack(pady=10)

    # Área de feedback com scrollbar
    frame_scroll = tk.Frame(root)
    frame_scroll.pack(pady=10, fill=tk.BOTH, expand=True)

    canvas_feedback = tk.Canvas(frame_scroll, height=250)
    scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas_feedback.yview)
    canvas_feedback.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas_feedback.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    quadro_feedback = tk.Frame(canvas_feedback)
    canvas_feedback.create_window((0, 0), window=quadro_feedback, anchor="nw")

    # Atualiza a região de rolagem automaticamente
    quadro_feedback.bind("<Configure>", lambda e: canvas_feedback.configure(scrollregion=canvas_feedback.bbox("all")))

    # Botão para reiniciar o jogo manualmente
    botao_iniciar = tk.Button(root, text="Iniciar Jogo", font=("Arial", 18),
                              command=lambda: iniciar_jogo(estado, palavras, label_tentativas, quadro_feedback, canvas_feedback))
    botao_iniciar.pack(pady=20)

    # Começa o jogo automaticamente ao iniciar o programa
    iniciar_jogo(estado, palavras, label_tentativas, quadro_feedback, canvas_feedback)

    # Inicia o loop da interface gráfica
    root.mainloop()

# Roda o programa
main()
