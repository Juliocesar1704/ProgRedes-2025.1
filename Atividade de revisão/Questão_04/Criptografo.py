import os

# Aplica XOR entre os dados e a senha fornecida.
def aplicar_xor(dados, senha):
    senha_ascii = [ord(c) for c in senha]
    resultado = bytearray()
    for i in range(len(dados)):
        byte_original = dados[i]
        byte_senha = senha_ascii[i % len(senha_ascii)]
        resultado.append(byte_original ^ byte_senha)
    return resultado

# Criptografa o arquivo de origem com a senha e salva no destino.
def criptografar_arquivo(origem, senha, destino):
    try:
        if not os.path.isfile(origem):
            print(f"\n[❌] Erro: o arquivo de origem '{origem}' não foi encontrado.")
            return

        if os.path.exists(destino):
            print(f"\n[⚠️] Atenção: o arquivo de destino '{destino}' já existe. Escolha outro nome.")
            return

        with open(origem, 'rb') as arquivo:
            dados = arquivo.read()

        dados_criptografados = aplicar_xor(dados, senha)

        with open(destino, 'wb') as arquivo:
            arquivo.write(dados_criptografados)

        print(f"\n[✅] Sucesso: o arquivo foi criptografado como '{destino}'.")

    except Exception as erro:
        print(f"\n[🔥] Erro inesperado: {erro}")

# Função principal que interage com o usuário.
# Solicita o nome do arquivo de origem, a senha e o nome do arquivo de destino.
def main():
   
    print("\n=== 🚀 Programa de Criptografia XOR ===\n")

    origem = input("[📂] Informe o nome do arquivo de origem: ").strip()
    senha = input("[🔑] Informe a palavra-passe (senha): ").strip()
    destino = input("[💾] Informe o nome do arquivo de destino: ").strip()

    criptografar_arquivo(origem, senha, destino)

if __name__ == "__main__":
    main()
