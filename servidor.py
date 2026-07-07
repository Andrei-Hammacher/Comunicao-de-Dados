import socket
import struct
from protocolo import Frame

def recv_all(sock, num_bytes):
    data = bytearray()
    while len(data) < num_bytes:
        try:
            packet = sock.recv(num_bytes - len(data))
            if not packet: return None
            data.extend(packet)
        except socket.timeout:
            return None
    return bytes(data)

def iniciar_servidor():
    HOST, PORT = '127.0.0.1', 5000
    sequencia_esperada = 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor ARQ aguardando conexões na porta {PORT}...")
        
        conn, addr = s.accept()
        with conn:
            print(f"Conectado a {addr}\n")
            while True:
                header_bytes = recv_all(conn, Frame.HEADER_SIZE)
                if not header_bytes: break
                
                _, _, error_mode, payload_length, _, _ = struct.unpack(Frame.HEADER_FORMAT, header_bytes)
                payload_bytes = recv_all(conn, payload_length)
                trailer_bytes = recv_all(conn, 1) if error_mode == Frame.MODO_CRC else None
                
                quadro = Frame.from_bytes(header_bytes, payload_bytes, trailer_bytes)
                
                if quadro.frame_type == 0:
                    # Integração: Se o CRC acusar erro, descarta o quadro SILENCIOSAMENTE!
                    if quadro.corrompido:
                        print(f"[DESCARTADO] Quadro {quadro.seq_num} isolado devido a erro de CRC. Forçando Timeout no emissor...")
                        continue 
                    
                    if quadro.seq_num == sequencia_esperada:
                        print(f"[RECEBIDO] Quadro {quadro.seq_num} intacto. Mensagem: {quadro.payload.decode('utf-8')}")
                        
                        # Responde com ACK (utilizando o mesmo modo de erro da conexão)
                        ack_frame = Frame(src=quadro.dst, dst=quadro.src, payload=b'', error_mode=error_mode, seq_num=sequencia_esperada, frame_type=1)
                        conn.sendall(ack_frame.to_bytes())
                        sequencia_esperada += 1
                    else:
                        print(f"[FORA DE ORDEM] Quadro {quadro.seq_num} recebido, mas esperava {sequencia_esperada}.")
                        if sequencia_esperada > 0:
                            ack_frame = Frame(src=quadro.dst, dst=quadro.src, payload=b'', error_mode=error_mode, seq_num=sequencia_esperada - 1, frame_type=1)
                            conn.sendall(ack_frame.to_bytes())

if __name__ == "__main__":
    iniciar_servidor()