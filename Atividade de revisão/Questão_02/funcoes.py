import hashlib
import time

# Função para calcular o hash SHA-256
# e encontrar o nonce que gera um hash com os bits iniciais zerados
# Entrada: dados para hash e número de bits zerados
# Saída: nonce encontrado e tempo gasto
def findNonce(dataToHash: bytes, bitsToBeZero: int):
    start_time = time.time()
    nonce = 0
    while True:
        entrada = nonce.to_bytes(4, 'big') + dataToHash
        hash_resultado = hashlib.sha256(entrada).hexdigest()
        hash_bin = bin(int(hash_resultado, 16))[2:].zfill(256)
        if hash_bin.startswith('0' * bitsToBeZero):
            break
        nonce += 1
    elapsed_time = time.time() - start_time
    return nonce, elapsed_time
