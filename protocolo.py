import struct

class Frame:
    HEADER_FORMAT = '!BBH' 
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, src: int, dst: int, payload: bytes, error_check: int = 0):
        self.src = src
        self.dst = dst
        self.payload = payload
        self.error_check = error_check

    def to_bytes(self) -> bytes:
        payload_length = len(self.payload)
        header = struct.pack(self.HEADER_FORMAT, self.src, self.dst, payload_length)
        return header + self.payload

    @classmethod
    def from_bytes(cls, header_data: bytes, payload_data: bytes):
        """Reconstrução separada para facilitar o uso com sockets (que leem em partes)"""
        src, dst, payload_length = struct.unpack(cls.HEADER_FORMAT, header_data)
        return cls(src=src, dst=dst, payload=payload_data)