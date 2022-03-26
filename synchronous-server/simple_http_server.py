import socket
import sys

# Standard loop-back interface address
SERVER_HOST = '127.0.0.1'

# Non-privileged ports are > 1023
SERVER_PORT = 8888


class SimpleServer:
    """
    Implementation of a simple HTTP/2.0 Server using TCP socket programming.
    The server accepts any type of client requests and responds with a hello
    world text.

        Limitations:
        1) The server is not capable of handling concurrent client requests.
        2) It needs to be ensured that all client request data is received
           to handle the cases where request data is greater than receive
           buffer size.

        Phases of HTTP message exchange over TCP by the server:
            Server: socket -> bind -> listen -> accept -> recv -> send -> recv -> close
    """

    def __init__(self, host: str, port: int):
        self.__create_socket(host, port)
        self.__make_listening_socket()

    def __create_socket(self, host: str, port: int) -> socket:
        try:
            # AF_INET - IPv4 address family, SOCK_STREAM - TCP (connection-based)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable address re-usability
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((host, port))
        except socket.error:
            print(f'Error creating server socket', file=sys.stderr)
            raise

    def __make_listening_socket(self):
        # 1 is the max length of the pending connections queue (backlog)
        self.socket.listen(1)
        print(f'Server listening at: http://{SERVER_HOST}:{SERVER_PORT}')

    def accept_any_request(self) -> tuple[socket, tuple[str, str]]:
        """
        Accepts any type of client request.

        :return: Client connection socket and the connected client information.

        :raises TypeError: When the server socket cannot be found.
        """

        if not hasattr(self, 'socket') or not self.socket:
            raise TypeError(
                '\'NoneType\' server socket found. Cannot accept requests.')

        return self.socket.accept()

    def close_server_socket(self):
        if not hasattr(self, 'socket') or not self.socket:
            return

        self.socket.close()


if __name__ == "__main__":
    server = SimpleServer(SERVER_HOST, SERVER_PORT)
    try:
        while True:
            connection, client_address = server.accept_any_request()
            print(f'Connected by {client_address}')

            with connection:
                # 1024 is the buffer size in bytes
                request_data = connection.recv(1024)
                # avoid the issue of byte ordering
                # request_data.decode('utf-8')

                # status code and content must be separated by blank lines
                response = 'HTTP/2.0 200 OK\n\nHello World!'
                connection.sendall(response.encode())
    except Exception:
        print(f'Server encountered an error.', file=sys.stderr)
        raise
    finally:
        server.close_server_socket()
