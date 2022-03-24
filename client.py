import argparse
import os
import socket

HOST = '127.0.0.1'
PORT = 8888


class Client:
    """
    Implementation of a client using TCP socket programming that
    can establish multiple client connections and send simple message
    to the standard loop-back interface address.

    Phases of HTTP message exchange over TCP by the client:
        Client: socket -> connect -> send -> recv -> close
    """

    def __init__(self):
        self.__initialize_args()
        self.__send_requests()

    def __initialize_args(self):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '--max-conns',
            type=int,
            default=1,
            help='Maximum number of connections per client.'
        )

        parser.add_argument(
            '--max-clients',
            type=int,
            default=1,
            help='Maximum number of clients.'
        )

        self.args = parser.parse_args()

    def __send_requests(self):

        for client_num in range(1, self.args.max_clients + 1):
            pid = os.fork()

            if pid != 0:
                continue

            print(f'Client: {client_num}')

            for connection_num in range(1, self.args.max_conns + 1):
                # AF_INET - IPv4 address family, SOCK_STREAM - TCP (connection-based)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((HOST, PORT))
                    request_message = b"Hello!"
                    client_socket.sendall(request_message)
                    response = client_socket.recv(1024)

                    print(f'Connection number: {connection_num}')
                    print(f'Response: {response}')
                    os._exit(0)


if __name__ == "__main__":
    Client()
