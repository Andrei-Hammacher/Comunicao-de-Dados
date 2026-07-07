import socket
import struct
import argparse
from protocolo import Frame

def iniciar_cliente():
    parser = argparse.ArgumentParser(description="Emissor ARQ com Controle de Erro")
    parser.add_argument('--modo', choices=['crc', 'hamming'], required=True)
    parser.add_argument('--ruido', action='store_true', help="Corrompe o Quadro 2 para teste")
    parser.add_argument('--perda', action='store_true', help="Derruba o Quadro 2 na rede (simula perda física)")
    args = parser.parse_args()

    HOST, PORT = '127.0.0.1', 5000
    TAMANHO_JANELA = 3
    TIMEOUT = 2.0
    MODO_INT = Frame.MODO_CRC if args.modo == 'crc' else Frame.MODO_HAMMING
    
    mensagens = [f"Carga de Dados {letra}".encode('utf-8') for letra in ['A', 'B', 'C', 'D', 'E']]
    total_pacotes = len(mensagens)
    base, proximo_seq = 0, 0
    historico_ruido = set() # Evita corromper infinitamente o mesmo quadro

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.settimeout(TIMEOUT)
        print(f"Iniciando transmissão Go-Back-N via {args.modo.upper()}...\n")
        
        while base < total_pacotes:
            while proximo_seq < base + TAMANHO_JANELA and proximo_seq < total_pacotes:
                quadro = Frame(src=15, dst=42, payload=mensagens[proximo_seq], error_mode=MODO_INT, seq_num=proximo_seq, frame_type=0)
                dados = bytearray(quadro.to_bytes())

                # SIMULADORES PARA APRESENTAÇÃO (Atingem o Quadro 2)
                pular_envio = False
                if proximo_seq == 2 and proximo_seq not in historico_ruido:
                    if args.perda:
                        print(f"[SIMULADOR] Quadro {proximo_seq} 'perdido' na fiação (não enviado).")
                        pular_envio = True
                        historico_ruido.add(proximo_seq)
                    elif args.ruido:
                        print(f"[SIMULADOR] Injetando ruído no payload do Quadro {proximo_seq}...")
                        if args.modo == 'crc': dados[6] ^= 0xFF
                        else: dados[6] = ord('1') if dados[6] == ord('0') else ord('0')
                        historico_ruido.add(proximo_seq)

                if not pular_envio:
                    s.sendall(dados)
                    print(f"[ENVIADO] Quadro {proximo_seq}")
                proximo_seq += 1
                
            try:
                while base < proximo_seq:
                    header_bytes = s.recv(Frame.HEADER_SIZE)
                    if not header_bytes: break
                    
                    _, _, _, payload_length, ack_num, frame_type = struct.unpack(Frame.HEADER_FORMAT, header_bytes)
                    
                    if payload_length > 0: s.recv(payload_length)
                    if MODO_INT == Frame.MODO_CRC: s.recv(1) # Lê o trailer do ACK
                        
                    if frame_type == 1:
                        print(f"[ACK] Confirmação recebida do Quadro {ack_num}")
                        if ack_num >= base:
                            base = ack_num + 1 
            except socket.timeout:
                print(f"\n[TIMEOUT] Estouro de tempo aguardando ACKs! Retrocedendo janela para o quadro {base}...\n")
                proximo_seq = base 
                
        print("\n[SUCESSO] Transmissão completa!")

if __name__ == "__main__":
    iniciar_cliente()