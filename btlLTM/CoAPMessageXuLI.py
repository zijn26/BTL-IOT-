
"""
CoAP Message Parser và Builder
Đơn giản hóa cho mục đích học tập
"""
import struct
import socket
from enum import IntEnum
from typing import Dict, List, Tuple, Optional

class CoAPType(IntEnum):
    """CoAP Message Types"""
    CON = 0  # Confirmable
    NON = 1  # Non-confirmable
    ACK = 2  # Acknowledgement
    RST = 3  # Reset

class CoAPCode(IntEnum):
    """CoAP Method Codes và Response Codes"""
    # Request Methods
    GET = 1       # phan code cua goi tin la GET
    POST = 2       # phan code cua goi tin la POST
    PUT = 3       # phan code cua goi tin la PUT
    DELETE = 4       # phan code cua goi tin la DELETE

    # Response Codes
    CREATED = 65      # 2.01  server phan hoi lai da tao tai nguyen thanh cong
    DELETED = 66      # 2.02  server phan hoi lai da xoa tai nguyen thanh cong
    CHANGED = 68      # 2.04  server phan hoi lai da thay doi tai nguyen thanh cong
    CONTENT = 69      # 2.05  server phan hoi lai da tra ve noi dung tai nguyen

    BAD_REQUEST = 128   # 4.00
    NOT_FOUND = 132     # 4.04
    METHOD_NOT_ALLOWED = 133  # 4.05

    INTERNAL_SERVER_ERROR = 160  # 5.00

class CoAPOption(IntEnum):
    """CoAP Option Numbers - chỉ implement các option cơ bản"""
    URI_PATH = 11
    CONTENT_FORMAT = 12
    URI_QUERY = 15

class CoAPContentFormat(IntEnum):
    """CoAP Content-Format numbers (subset)"""
    JSON = 50  # application/json

class CoAPMessage:
    """CoAP Message Class đơn giản"""

    def __init__(self):
        self.version = 1
        self.msg_type = CoAPType.CON
        self.token_length = 0
        self.code = CoAPCode.GET
        self.message_id = 0
        self.token = b''
        self.options = []  # List of (option_number, option_value)
        self.payload = b''

    @classmethod
    def from_bytes(cls, data: bytes) -> 'CoAPMessage': 
        """Parse CoAP message từ bytes"""
        if len(data) < 4:
            raise ValueError("CoAP message quá ngắn")

        msg = cls()

        # Parse header (4 bytes)
        first_byte = data[0]
        msg.version = (first_byte >> 6) & 0x3
        msg.msg_type = CoAPType((first_byte >> 4) & 0x3)
        msg.token_length = first_byte & 0xF

        msg.code = CoAPCode(data[1])
        msg.message_id = struct.unpack('!H', data[2:4])[0]

        pos = 4

        # Parse token
        if msg.token_length > 0:
            msg.token = data[pos:pos + msg.token_length]
            pos += msg.token_length

        # Parse options (đơn giản hóa - chỉ support options cơ bản)
        option_number = 0
        while pos < len(data) and data[pos] != 0xFF:
            delta = (data[pos] >> 4) & 0xF
            length = data[pos] & 0xF
            pos += 1

            option_number += delta
            if length > 0:
                option_value = data[pos:pos + length]
                msg.options.append((option_number, option_value))
                pos += length

        # Parse payload
        if pos < len(data) and data[pos] == 0xFF:
            pos += 1  # Skip payload marker
            msg.payload = data[pos:]

        return msg

    def to_bytes(self) -> bytes:
        """Convert CoAP message thành bytes"""
        # Build header
        first_byte = (self.version << 6) | (self.msg_type << 4) | self.token_length
        header = struct.pack('!BBH', first_byte, self.code, self.message_id)
        # !: network byte order (big-endian), kích thước chuẩn.
        # B: unsigned char, 1 byte (0–255).
        # B: unsigned char, 1 byte (0–255).
        # H: unsigned short, 2 byte (0–65535).
        # Tổng cộng 4 byte, theo thứ tự: byte1 = a, byte2 = b, byte3-4 = c (big-endian: byte cao của c trước).
        result = header + self.token
 
        # Build options (đơn giản hóa)
        last_option_number = 0
        for option_number, option_value in sorted(self.options):
            delta = option_number - last_option_number
            length = len(option_value)

            # Đơn giản hóa: chỉ support delta và length < 13
            if delta < 13 and length < 13:
                result += bytes([(delta << 4) | length])
                result += option_value
                last_option_number = option_number

        # Add payload
        if self.payload:
            result += b'\xff'  # Payload marker
            result += self.payload

        return result

    def add_option(self, option_number: int, option_value: bytes):
        """Thêm option vào message"""
        self.options.append((option_number, option_value))

    def set_content_format(self, format_value: int):
        """Set Content-Format option (numeric)."""
        # Remove existing CONTENT_FORMAT
        self.options = [(num, val) for num, val in self.options if num != CoAPOption.CONTENT_FORMAT]
        # Encode unsigned int in minimal bytes (big-endian)
        if format_value < 0:
            format_value = 0
        if format_value == 0:
            encoded = b"\x00"
        else:
            value = format_value
            bytes_required = (value.bit_length() + 7) // 8
            encoded = value.to_bytes(bytes_required, 'big')
        self.add_option(CoAPOption.CONTENT_FORMAT, encoded)

    def get_content_format(self) -> Optional[int]:
        """Get Content-Format option if present."""
        for num, val in self.options:
            if num == CoAPOption.CONTENT_FORMAT:
                try:
                    return int.from_bytes(val, 'big') if val else 0
                except Exception:
                    return None
        return None

    def get_uri_path(self) -> str:
        """Lấy URI path từ options"""
        path_segments = []
        for option_number, option_value in self.options:
            if option_number == CoAPOption.URI_PATH:
                path_segments.append(option_value.decode('utf-8'))
        return '/' + '/'.join(path_segments) if path_segments else '/'

    def set_uri_path(self, path: str):
        """Set URI path"""
        # Remove existing URI_PATH options
        self.options = [(num, val) for num, val in self.options 
                       if num != CoAPOption.URI_PATH]

        # Add new URI_PATH options
        if path.startswith('/'):
            path = path[1:]

        for segment in path.split('/'):
            if segment:
                self.add_option(CoAPOption.URI_PATH, segment.encode('utf-8'))

    def __str__(self):
        return (f"CoAP(type={self.msg_type.name}, code={self.code}, "
                f"id={self.message_id}, uri={self.get_uri_path()}, "
                f"payload_len={len(self.payload)})")

def create_response(request: CoAPMessage, code: CoAPCode, payload: bytes = b'') -> CoAPMessage:
    """Tạo CoAP response từ request"""
    response = CoAPMessage()
    response.version = 1
    response.msg_type = CoAPType.ACK if request.msg_type == CoAPType.CON else CoAPType.NON
    response.code = code
    response.message_id = request.message_id
    response.token = request.token
    response.token_length = len(response.token)
    response.payload = payload
    return response

def create_request(method: CoAPCode, uri_path: str, payload: bytes = b'') -> CoAPMessage:
    """Tạo CoAP request"""
    import random

    request = CoAPMessage()
    request.version = 1
    request.msg_type = CoAPType.CON
    request.code = method
    request.message_id = random.randint(1, 65535)
    request.set_uri_path(uri_path)
    request.payload = payload
    # If payload looks like JSON, set Content-Format to application/json
    try:
        if payload and (payload.strip().startswith(b'{') or payload.strip().startswith(b'[')):
            request.set_content_format(CoAPContentFormat.JSON)
    except Exception:
        pass
    return request
