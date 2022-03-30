import errno
import os
import signal
import socket
import sys


class ConcurrentServer:
    """
    Implementation of a concurrent HTTP Server using TCP socket programming.
    The server accepts any type of client requests and responds with a hello
    world text.

    It is capable of serving multiple client requests concurrently and ensures
    that no zombie processes are created while spawning and handling child processes.

    Limitations:
    1) It needs to be ensured that all client request data is received
        to handle the cases where request data is greater than receive
        buffer size.

    Phases of HTTP message exchange over TCP by the server:
        Server: socket -> bind -> listen -> accept -> recv -> send -> recv -> close
    """

    def __init__(self, host: str, port: int):
        self.HOST = host
        self.PORT = port
        self.REQUEST_QUEUE_LIMIT = 1024

        self.__create_socket()
        self.__make_listening_socket()
        self.__register_signal_handlers()

    def __create_socket(self):
        try:
            # AF_INET - IPv4 address family, SOCK_STREAM - TCP (connection-based)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Enable address re-usability
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.HOST, self.PORT))
        except socket.error:
            print(f'Error creating server socket', file=sys.stderr)
            raise

    def __sigtstp_signal_handler(self, signum, frame):
        self.close_socket()
        sys.exit(0)

    def __sigchld_signal_handler(self, signum, frame):
        # wait for all child processes to prevent zombies
        while True:
            try:
                # -1: wait for termination of any child process
                # os.WNOHANG: returns (0, 0) when no child process status is available
                pid, status = os.waitpid(-1, os.WNOHANG)

                if pid == 0 and status == 0:
                    return
            except OSError:
                return

    def __register_signal_handlers(self):
        signal.signal(signal.SIGCHLD, self.__sigchld_signal_handler)
        # close socket if process is suspended
        signal.signal(signal.SIGTSTP, self.__sigtstp_signal_handler)

    def __make_listening_socket(self):
        # 1 is the max length of the pending connections queue (backlog)
        self.socket.listen(self.REQUEST_QUEUE_LIMIT)
        print(f'Server listening at: http://{self.HOST}:{self.PORT}')

    def accept_any_request(self) -> tuple[socket, tuple[str, str]]:
        """
        Accepts any type of client request.

        :return: Client connection socket and the connected client information.

        :raises `TypeError`: When the server socket cannot be found.
        """

        if not hasattr(self, 'socket') or not self.socket:
            raise TypeError(
                '\'NoneType\' server socket found. Cannot accept requests.')

        return self.socket.accept()

    def handle_request(self, client_connection: socket):
        # 1024 is the buffer size in bytes
        request_data = client_connection.recv(1024)
        # avoid the issue of byte ordering
        # request_data.decode('utf-8')

        # status code and content must be separated by blank lines
        response = 'HTTP/1.0 200 OK\n\nHello World!'
        client_connection.sendall(response.encode())

    def close_socket(self):
        if not hasattr(self, 'socket') or not self.socket:
            return

        self.socket.close()


if __name__ == "__main__":

    # Standard loop-back interface address
    SERVER_HOST = '127.0.0.1'
    # Non-privileged ports are > 1023
    SERVER_PORT = 8888

    server = ConcurrentServer(SERVER_HOST, SERVER_PORT)

    try:
        while True:
            try:
                connection, client_address = server.accept_any_request()
                print(f'Connected by {client_address}')
            except IOError as e:
                code, message = e.args
                # retry accept if it was interrupted
                if code == errno.EINTR:
                    continue
                raise

            pid = os.fork()

            if pid == 0:
                # close child copy
                # this ensures correct descriptor reference count
                server.close_socket()

                with connection:
                    server.handle_request(connection)

                os._exit(os.EX_OK)
            else:
                # close parent copy
                connection.close()

    except Exception:
        print(f'Server encountered an error.', file=sys.stderr)
        raise
    finally:
        server.close_socket()
