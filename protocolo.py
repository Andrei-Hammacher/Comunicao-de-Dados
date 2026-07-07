import struct

# --- Matemática CRC ---
def calcular_crc(dados_bin: str, polinomio: str) -> str:
    if not dados_bin: return '0' * (len(polinomio)-1)
    grau = len(polinomio) - 1
    mensagem = list(dados_bin + ('0' * grau))
    poli = list(polinomio)
    for i in range(len(dados_bin)):
        if mensagem[i] == '1':
            for j in range(len(polinomio)):
                mensagem[i+j] = str(int(mensagem[i+j]) ^ int(poli[j]))
    return ''.join(mensagem)[-grau:]

def verificar_crc(dados_recebidos: str, crc_recebido: str, polinomio: str) -> bool:
    return int(calcular_crc(dados_recebidos + crc_recebido, polinomio)) == 0

# --- Matemática Hamming ---
def codificar_hamming(dados_bin: str) -> str:
    if not dados_bin: return ''
    n, r = len(dados_bin), 0
    while (2**r < n + r + 1): r += 1
    tamanho_total = n + r
    resultado = ['0'] * tamanho_total
    j = 0
    for i in range(1, tamanho_total + 1):
        if (i & (i - 1)) != 0:
            resultado[i-1] = dados_bin[j]
            j += 1
    for i in range(r):
        posicao = 2**i
        soma = 0
        for k in range(1, tamanho_total + 1):
            if k & posicao: soma ^= int(resultado[k-1])
        resultado[posicao-1] = str(soma)
    return ''.join(resultado)

def decodificar_hamming(dados_recebidos: str) -> tuple[bool, str]:
    if not dados_recebidos: return False, ''
    r = 0
    while (2**r <= len(dados_recebidos)): r += 1
    sindrome = 0
    for i in range(r):
        posicao = 2**i
        soma = 0
        for k in range(1, len(dados_recebidos) + 1):
            if k & posicao: soma ^= int(dados_recebidos[k-1])
        if soma != 0: sindrome += posicao
            
    lista_bits = list(dados_recebidos)
    houve_correcao = False
    if 0 < sindrome <= len(lista_bits):
        bit = sindrome - 1
        lista_bits[bit] = '1' if lista_bits[bit] == '0' else '0'
        houve_correcao = True

    mensagem_original = []
    for i in range(1, len(lista_bits) + 1):
        if (i & (i - 1)) != 0: mensagem_original.append(lista_bits[i-1])
    return houve_correcao, ''.join(mensagem_original)

# --- Protocolo Híbrido (Erro + Fluxo) ---
class Frame:
    # Origem(B), Destino(B), Modo(B), Tamanho(H), Seq(H), Tipo(B)
    HEADER_FORMAT = '!BBBHHB' 
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    POLINOMIO_CRC = '100000111'
    MODO_CRC = 1
    MODO_HAMMING = 2

    def __init__(self, src: int, dst: int, payload: bytes, error_mode: int, seq_num: int = 0, frame_type: int = 0, error_check: int = 0, corrompido: bool = False):
        self.src = src
        self.dst = dst
        self.payload = payload
        self.error_mode = error_mode
        self.seq_num = seq_num
        self.frame_type = frame_type
        self.error_check = error_check
        self.corrompido = corrompido # Flag para avisar o servidor se o CRC falhou

    def to_bytes(self) -> bytes:
        bits_mensagem = ''.join(format(byte, '08b') for byte in self.payload)
        
        if self.error_mode == self.MODO_CRC:
            header = struct.pack(self.HEADER_FORMAT, self.src, self.dst, self.error_mode, len(self.payload), self.seq_num, self.frame_type)
            crc_str = calcular_crc(bits_mensagem, self.POLINOMIO_CRC)
            self.error_check = int(crc_str, 2)
            trailer = struct.pack('!B', self.error_check)
            return header + self.payload + trailer
            
        elif self.error_mode == self.MODO_HAMMING:
            bits_hamming = codificar_hamming(bits_mensagem)
            payload_rede = bits_hamming.encode('utf-8')
            header = struct.pack(self.HEADER_FORMAT, self.src, self.dst, self.error_mode, len(payload_rede), self.seq_num, self.frame_type)
            return header + payload_rede

    @classmethod
    def from_bytes(cls, header_data: bytes, payload_data: bytes, trailer_data: bytes = None):
        src, dst, error_mode, _, seq_num, frame_type = struct.unpack(cls.HEADER_FORMAT, header_data)
        
        if error_mode == cls.MODO_CRC:
            error_check = struct.unpack('!B', trailer_data)[0] if trailer_data else 0
            corrompido = False
            
            # Só faz verificação se for um quadro de dados (ignora ACKs vazios)
            if frame_type == 0 and len(payload_data) > 0:
                grau = len(cls.POLINOMIO_CRC) - 1
                crc_str = format(error_check, f'0{grau}b')
                bits_mensagem = ''.join(format(byte, '08b') for byte in payload_data)
                if not verificar_crc(bits_mensagem, crc_str, cls.POLINOMIO_CRC):
                    corrompido = True
                    print(f"[X] CRC ALERTA! Quadro {seq_num} corrompido na rede.")
                    
            return cls(src, dst, payload_data, error_mode, seq_num, frame_type, error_check, corrompido)
            
        elif error_mode == cls.MODO_HAMMING:
            bits_recebidos = payload_data.decode('utf-8')
            corrigido, bits_limpos = decodificar_hamming(bits_recebidos)
            
            if frame_type == 0 and corrigido:
                print(f"[!] HAMMING: Erro no Quadro {seq_num} detectado e CORRIGIDO na hora!")
                
            bytes_restaurados = bytearray()
            for i in range(0, len(bits_limpos), 8):
                byte_str = bits_limpos[i:i+8]
                if len(byte_str) == 8: bytes_restaurados.append(int(byte_str, 2))
                
            return cls(src, dst, bytes(bytes_restaurados), error_mode, seq_num, frame_type, 0, False)