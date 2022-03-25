import argparse
import selectors
import socket


class Client:
    """
    Implementation of a client using TCP socket programming and
    python `selectors` module that can establish multiple client
    connections and send messages to the standard loop-back
    interface address.

    Usage: `python3 client.py --max-conns=<int>`
    max-conns = Maximum client connections to the server (default = 1)

    Phases of HTTP message exchange over TCP by the client:
        Client: socket -> connect -> send -> recv -> close
    """

    def __init__(self, server_host: str, server_port: int, max_connections: int):
        self.HOST = server_host
        self.PORT = server_port
        self.max_connections = max_connections
        self.messages_to_send = ['Message 1', 'Message 2']
        self.selector = selectors.DefaultSelector()

    def __handle_socket_ready_event(self, key: selectors.SelectorKey, mask: int):
        connection = key.fileobj
        data = key.data

        if mask & selectors.EVENT_READ:
            received_data = connection.recv(1024)

            if received_data:
                received_data = received_data.decode('utf-8')
                print(f'Received message: {received_data}')
            else:
                self.selector.unregister(connection)
                connection.close()

        if mask & selectors.EVENT_WRITE:

            if not data.get_output_buffer() and data.get_request_data():
                data.set_output_buffer(
                    data.get_request_data().pop(0).encode())

            if data.get_output_buffer():
                buffer = data.get_output_buffer()

                print(f'Sending {buffer}')

                bytes_sent = connection.send(buffer)
                data.set_output_buffer(buffer[bytes_sent:])

    def __process_ready_socket_events(self):
        try:
            connection = None

            while True:
                ready_events = self.selector.select()
                for key, mask in ready_events:
                    connection = key.fileobj
                    self.__handle_socket_ready_event(key, mask)
        except:
            raise
        finally:
            if connection:
                self.selector.unregister(connection)
                connection.close()

    def send_requests(self):
        """
        Initiates client connections equal to the maximum connections parameter.
        All messages are sent sequentially through the connection request.
        """

        for connection_num in range(1, self.max_connections + 1):
            print(f'Connection {connection_num} to {self.HOST}:{self.PORT}')
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.setblocking(False)
            connection.connect_ex((self.HOST, self.PORT))
            waited_events = selectors.EVENT_READ | selectors.EVENT_WRITE
            payload = self.RequestPayload(
                request_data=self.messages_to_send.copy())

            self.selector.register(connection, waited_events, payload)
            connection_num = connection_num + 1

        self.__process_ready_socket_events()

    class RequestPayload:
        """
        Helper class to wrap the request data and output
        buffer for a client connection processing.
        """
        __request_data = b''
        __output_buffer = b''

        def __init__(self, request_data: bytes):
            self.__request_data = request_data

        def get_request_data(self) -> bytes:
            return self.__request_data

        def set_request_data(self, new_data: bytes):
            self.__request_data = new_data

        def get_output_buffer(self) -> bytes:
            return self.__output_buffer

        def set_output_buffer(self, new_data: bytes):
            self.__output_buffer = new_data


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--max-conns',
        type=int,
        default=1,
        help='Maximum number of connections per client.'
    )

    max_conns = parser.parse_args().max_conns
    max_conns = max_conns if max_conns > 0 else 1

    client = Client(server_host='127.0.0.1', server_port=8888,
                    max_connections=max_conns)
    client.send_requests()
