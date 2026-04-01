import os

IP = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 4096

ENCODING = "utf-8"
HEADER_SIZE = 10

# Пути к папкам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_STORAGE = os.path.join(BASE_DIR, "server", "storage")
CLIENT_DOWNLOADS = os.path.join(BASE_DIR, "client", "downloads")

os.makedirs(SERVER_STORAGE, exist_ok=True)
os.makedirs(CLIENT_DOWNLOADS, exist_ok=True)

CMD_LIST = "LIST"
CMD_DOWNLOAD = "DOWNLOAD"
CMD_UPLOAD = "UPLOAD"
CMD_EXIT = "EXIT"

STATUS_OK = "OK"
STATUS_ERROR = "ERROR"


def send_msg(sock, message):
    data = message.encode(ENCODING)
    header = f"{len(data):<{HEADER_SIZE}}".encode(ENCODING)
    sock.sendall(header + data)


def recv_msg(sock):
    raw_header = sock.recv(HEADER_SIZE)
    if not raw_header: return None
    size = int(raw_header.decode(ENCODING).strip())

    data = b""
    while len(data) < size:
        chunk = sock.recv(min(size - len(data), BUFFER_SIZE))
        if not chunk: break
        data += chunk
    return data.decode(ENCODING)