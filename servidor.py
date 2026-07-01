import socket
from protocolo import Frame

def recv_all(sock, num_bytes):
    """Garante a leitura exata de 'num_bytes' do socket."""
    data = bytearray()
    while len(data) < num_bytes:
        packet = sock.recv(num_bytes - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def iniciar_servidor():
    HOST = '127.0.0.1'
    PORT = 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor aguardando conexões em {HOST}:{PORT}...")
        
        conn, addr = s.accept()
        with conn:
            print(f"Conectado a {addr}")
            
            # 1. Lê exatamente o tamanho do cabeçalho (4 bytes)
            header_bytes = recv_all(conn, Frame.HEADER_SIZE)
            if not header_bytes:
                print("Conexão encerrada pelo cliente.")
                return
            
            # Descobre o tamanho do payload sem ler o resto ainda
            import struct
            _, _, payload_length = struct.unpack(Frame.HEADER_FORMAT, header_bytes)
            print(f"Cabeçalho recebido! Esperando payload de {payload_length} bytes...")

            # 2. Lê exatamente o tamanho do payload informado
            payload_bytes = recv_all(conn, payload_length)
            
            # 3. Reconstrói o quadro
            quadro = Frame.from_bytes(header_bytes, payload_bytes)
            
            print("\n--- QUADRO RECEBIDO COM SUCESSO ---")
            print(f"Origem: {quadro.src}")
            print(f"Destino: {quadro.dst}")
            print(f"Mensagem: {quadro.payload.decode('utf-8')}")

if __name__ == "__main__":
    iniciar_servidor()