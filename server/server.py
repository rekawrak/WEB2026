import socket
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import preferences


def handle_client(conn, addr):
    print(f"Соединение установлено: {addr}")
    try:
        while True:
            msg = preferences.recv_msg(conn)
            if not msg or msg.upper() == preferences.CMD_EXIT: break

            parts = msg.split(maxsplit=1)
            cmd = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            if cmd == preferences.CMD_LIST:
                files = [f for f in os.listdir(preferences.SERVER_STORAGE) if not f.startswith('.')]
                response = "\n".join(files) if files else "Папка пуста"
                preferences.send_msg(conn, response)

            elif cmd == preferences.CMD_UPLOAD and args:
                size_msg = preferences.recv_msg(conn)
                file_size = int(size_msg)
                file_path = os.path.join(preferences.SERVER_STORAGE, args)

                with open(file_path, "wb") as f:
                    remaining = file_size
                    while remaining > 0:
                        chunk = conn.recv(min(remaining, preferences.BUFFER_SIZE))
                        if not chunk: break
                        f.write(chunk)
                        remaining -= len(chunk)
                preferences.send_msg(conn, f"Файл {args} успешно загружен")

            elif cmd == preferences.CMD_DOWNLOAD and args:
                file_path = os.path.join(preferences.SERVER_STORAGE, args)
                if os.path.exists(file_path):
                    preferences.send_msg(conn, preferences.STATUS_OK)
                    size = os.path.getsize(file_path)
                    preferences.send_msg(conn, str(size))
                    with open(file_path, "rb") as f:
                        conn.sendall(f.read())
                else:
                    preferences.send_msg(conn, preferences.STATUS_ERROR)

            else:
                preferences.send_msg(conn, "Неизвестная команда")
    except Exception as e:
        print(f"Ошибка {addr}: {e}")
    finally:
        conn.close()
        print(f"Отключен клиент: {addr}")


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((preferences.IP, preferences.PORT))
    s.listen(5)
    print(f"Сервер запущен на {preferences.IP}:{preferences.PORT}")
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()


if __name__ == "__main__":
    start()