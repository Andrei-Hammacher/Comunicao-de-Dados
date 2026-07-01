import socket
from protocolo import Frame

def iniciar_cliente():
    HOST = '127.0.0.1'
    PORT = 5000

    # 1. Cria a mensagem e o quadro
    mensagem = "Fala servidor! Aqui é o cliente testando o Framing de tamanho variável."
    quadro = Frame(src=15, dst=42, payload=mensagem.encode('utf-8'))
    
    # Transforma em bytes puros
    dados_para_enviar = quadro.to_bytes()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Conectado ao servidor!")
        
        # 2. Envia tudo de uma vez
        s.sendall(dados_para_enviar)
        print(f"Enviado um quadro de {len(dados_para_enviar)} bytes no total.")

if __name__ == "__main__":
    iniciar_cliente()