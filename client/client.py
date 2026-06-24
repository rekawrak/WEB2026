import socket
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import preferences


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((preferences.IP, preferences.PORT))
        print("Подключено. Доступны команды: LIST, UPLOAD <file>, DOWNLOAD <file>, EXIT")

        while True:
            inp = input(">> ").strip()
            if not inp: continue

            parts = inp.split(maxsplit=1)
            cmd = parts[0].upper()
            filename = parts[1] if len(parts) > 1 else ""

            if cmd == preferences.CMD_EXIT:
                preferences.send_msg(s, cmd)
                break

            elif cmd == preferences.CMD_UPLOAD:
                if not os.path.exists(filename):
                    print("Файл не найден локально")
                    continue
                size = os.path.getsize(filename)
                if size == 0:
                    print("Ошибка: Попытка загрузить пустой файл")
                    continue
                preferences.send_msg(s, inp)
                size = os.path.getsize(filename)
                preferences.send_msg(s, str(size))
                with open(filename, "rb") as f:
                    s.sendall(f.read())
                print(preferences.recv_msg(s))

            elif cmd == preferences.CMD_DOWNLOAD:
                preferences.send_msg(s, inp)
                status = preferences.recv_msg(s)
                if status == preferences.STATUS_OK:
                    size = int(preferences.recv_msg(s))
                    path = os.path.join(preferences.CLIENT_DOWNLOADS, filename)
                    with open(path, "wb") as f:
                        received = 0
                        while received < size:
                            chunk = s.recv(min(size - received, preferences.BUFFER_SIZE))
                            f.write(chunk)
                            received += len(chunk)
                    print(f"Скачано в {path}")
                else:
                    print("Файл на сервере не найден")

            else:
                preferences.send_msg(s, inp)
                print(preferences.recv_msg(s))

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        s.close()


if __name__ == "__main__":
    main()