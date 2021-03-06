import selectors
import socket
import sys


class ConcurrentServer:
    """
    Implementation of a HTTP Server using TCP socket programming and python's `selectors`
    module that is able to handle multiple client connections. The server accepts any type
    of client requests and responds with the same message received in the request.

    The server is capable of receiving all the data sent by the client handling the scenarios 
    where request data is greater than receive buffer. This, it is able to call `send()` and `recv()`
    as many times as needed.

    Limitations:
        1) The server is not capable of handling concurrent client requests.

    Phases of HTTP message exchange over TCP by the server:
        Server: socket -> bind -> listen -> accept -> recv -> send -> recv -> close
    """

    def __init__(self, host: str, port: int):
        self.HOST = host
        self.PORT = port
        self.REQUEST_QUEUE_LIMIT = 1024
        self.selector = selectors.DefaultSelector()

        self.__create_socket()
        self.__make_listening_socket()
        self.__set_non_blocking_socket()
        self.__register_read_selector()

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

    def __register_read_selector(self):
        self.selector.register(self.socket, selectors.EVENT_READ, data=None)

    def __make_listening_socket(self):
        # 1 is the max length of the pending connections queue (backlog)
        self.socket.listen(self.REQUEST_QUEUE_LIMIT)
        print(f'Server listening at: http://{self.HOST}:{self.PORT}')

    def __set_non_blocking_socket(self):
        self.socket.setblocking(False)

    def __accept_connection_for_socket(self, ready_socket: socket):
        client_connection, client_address = ready_socket.accept()
        print(f'Received connection from {client_address}')

        client_connection.setblocking(False)
        waited_events = selectors.EVENT_READ | selectors.EVENT_WRITE
        payload = self.RequestPayload(client_address)
        self.selector.register(client_connection, waited_events, payload)

    def __handle_connection_request(self, key: selectors.SelectorKey, event_mask):
        client_socket = key.fileobj
        data = key.data

        if event_mask & selectors.EVENT_READ:
            received_data = client_socket.recv(1024)

            if received_data:
                data.append_to_request_data(received_data)
                print(f'Received: {received_data}')
            else:
                address = data.get_client_address()
                print(f'Terminating connection with {address}')
                self.selector.unregister(client_socket)
                client_socket.close()

        if event_mask & selectors.EVENT_WRITE:
            # request message is echoed back in the response
            request_data = data.get_request_data()

            if request_data:
                bytes_sent = client_socket.send(request_data)
                data.set_request_data(request_data[bytes_sent:])

    def service_requests(self):
        """
        Starts looking for ready socket events and handle them.
        When the server socket is ready, it starts accepting
        client requests. When a client connection socket
        is ready for either read or write events, data is received
        or sent using the socket.
        """
        try:
            while True:
                ready_events = self.selector.select()

                for key, event_mask in ready_events:
                    if key.data and isinstance(key.data, self.RequestPayload):
                        self.__handle_connection_request(key, event_mask)
                    elif not key.data:
                        # server socket ready for connections
                        self.__accept_connection_for_socket(key.fileobj)
        except:
            raise
        finally:
            self.close_socket()

    def close_socket(self):
        """
        Closes the server socket.
        """
        if not hasattr(self, 'socket') or not self.socket:
            return

        print('Stopping the server')
        self.selector.unregister(self.socket)
        self.selector.close()
        self.socket.close()

    class RequestPayload:
        """
        Helper class to wrap the client address, request data and output
        buffer for a client connection processing.
        """
        __client_address = ''
        __request_data = b''

        def __init__(self, client_address: str):
            self.__client_address = client_address

        def get_client_address(self) -> str:
            return self.__client_address

        def set_client_address(self, new_address: str):
            self.__client_address = new_address

        def get_request_data(self) -> bytes:
            return self.__request_data

        def set_request_data(self, new_data: bytes):
            self.__request_data = new_data

        def append_to_request_data(self, data: bytes):
            self.__request_data += data


if __name__ == "__main__":

    # Standard loop-back interface address
    SERVER_HOST = '127.0.0.1'
    # Non-privileged ports are > 1023
    SERVER_PORT = 8888

    try:
        server = ConcurrentServer(SERVER_HOST, SERVER_PORT)
        server.service_requests()
    except Exception:
        print(f'Server encountered an error.', file=sys.stderr)
        raise
    finally:
        server.close_socket()
