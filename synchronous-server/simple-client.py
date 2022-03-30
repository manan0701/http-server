import socket

HOST = '127.0.0.1'
PORT = 8888


class Client:
    """
    Implementation of a simple client using TCP socket programming that
    sends a simple message to the standard loop-back interface address.

    Phases of HTTP message exchange over TCP by the client:
        Client: socket -> connect -> send -> recv -> close
    """

    def __init__(self):
        # AF_INET - IPv4 address family, SOCK_STREAM - TCP (connection-based)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            request_message = b"Hello!"
            client_socket.sendall(request_message)
            response = client_socket.recv(1024)
            print(response)


if __name__ == "__main__":
    Client()
