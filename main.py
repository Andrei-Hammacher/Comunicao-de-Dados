import struct

class Frame:
    # Formato do struct:
    # 'B' = unsigned char (1 byte) para Origem
    # 'B' = unsigned char (1 byte) para Destino
    # 'H' = unsigned short (2 bytes) para Tamanho
    # O total do cabeçalho é de 4 bytes.
    HEADER_FORMAT = '!BBH' 
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, src: int, dst: int, payload: bytes, error_check: int = 0):
        self.src = src
        self.dst = dst
        self.payload = payload
        self.error_check = error_check # Placeholder para o CRC/Hamming

    def to_bytes(self) -> bytes:
        """Empacota o quadro para ser enviado pelo socket."""
        payload_length = len(self.payload)
        
        # Cria o cabeçalho
        header = struct.pack(self.HEADER_FORMAT, self.src, self.dst, payload_length)
        
        # O quadro completo é a junção das partes
        # (Posteriormente, adicionaremos o error_check no final)
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes):
        """Desempacota os bytes recebidos do socket de volta para um objeto Frame."""
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Dados insuficientes para ler o cabeçalho.")

        # Extrai o cabeçalho
        header_bytes = data[:cls.HEADER_SIZE]
        src, dst, payload_length = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Extrai o payload com base no tamanho lido
        payload = data[cls.HEADER_SIZE : cls.HEADER_SIZE + payload_length]
        
        return cls(src=src, dst=dst, payload=payload)

# --- Exemplo de uso ---
if __name__ == "__main__":
    # 1. Criando um quadro
    mensagem = b"Ola, mundo da camada de enlace!"
    quadro_original = Frame(src=10, dst=20, payload=mensagem)
    
    # 2. Transformando em bytes (o que vai pro socket)
    dados_para_rede = quadro_original.to_bytes()
    print(f"Bytes enviados: {dados_para_rede}")
    
    # 3. Reconstruindo no receptor
    quadro_recebido = Frame.from_bytes(dados_para_rede)
    print(f"Origem: {quadro_recebido.src}, Destino: {quadro_recebido.dst}")
    print(f"Mensagem: {quadro_recebido.payload.decode('utf-8')}")