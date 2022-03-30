# HTTP server using TCP sockets

Environment: python `3.10.0`

The repo contains three implementations of an HTTP server with different capabilities along with client programs
for testing the HTTP Request/Response model. The standard loop-back interface address (`localhost` or `127.0.0.1:8888`) is assigned to every server.

Creation and management of TCP connections are done by leveraging methods from Python's socket module(implements the socket API).

# Learnings

To send an HTTP request to a Web server, a browser or a client application first establish a TCP connection
with the Web server. To communicate over a network, programs use sockets.

### **Socket**

A socket is an abstraction of a communication endpoint that allows a program to communicate with another program using file descriptors.
This abstraction is provided by the operating system that allows the exchange of bytes through a network.

### **Socket pair**

TCP/IP socket pair is a 4-tuple that recognizes endpoints of a TCP connection including the local and foreign IP addresses with their ports. A socket pair acts as a unique identifier of every TCP connection.

### **Phases of the server:**

1. Socket creation - TCP/IP socket is created

2. Bind - The server binds the address, assigns an IP address and port to the socket. Here the port specified is a well-known port as it identifies a service to which a client can connect.

3. Listen - The socket is made to be of listening type (only by the server) which notifies the kernel to accept an incoming connection request for the socket.

4. Accept - At this stage, the server starts accepting client connections sequentially. On receiving a new connection, the connected client socket is returned. The server reads the request data from the client socket, comprehends it and sends a response back to the client. Then the server closes the client connection socket and resumes accepting new client connections.

### **Phases of the client:**

1. Socket creation - The socket is created
2. Connect - The client connects to the server using the remote IP address (or hostname) and port number. The client calls `connect()` to establish a connection to the server and initiate the three-way handshake. The client does not need to bind an address as a local IP address and the port is of no use to it. The kernel assigns a local IP address and an ephemeral port (short-lived) when the client is connecting to the remote address.

### **Process**

A process is defined as an instance of an executing program. When a program is executed, it is loaded into memory and an instance of that executing program is known as a process.

### **File descriptor**

It is a positive integer assigned to a process by the kernel when File I/O is performed or when a new socket is created. This pattern follows the saying that _"Everything in Unix is a file"_. Every open file of a process is referred to by a file descriptor. Thus, when reading or writing, a file is identified by its file descriptor.

To deal with files, high-level access is given to programming languages with abstractions like sockets but under the hood, in UNIX they are identified by their integer file descriptors. In Python `fileno()` can be used to get the file descriptor of a file. A socket also has a file descriptor assigned to it.

### **Fork**

`fork()` is a system call in UNIX systems to spawn a child process. The method call returns twice, once in the parent process and another time
in the child process. In the child process, `fork()` returns 0 and in the parent process, the process id of the child process is returned.
When implementing a concurrent server using `fork()` it is important to note that when a parent forks a new child, the child gets a copy
of the parent's file descriptors. The kernel uses a reference count to determine whether or not a socket should be closed. After fork,
the child gets file descriptors of the parent and thus, the kernel increments their reference counts.

In the context of a concurrent server that spawns child process for request handling, if duplicate file descriptors are not closed, the client connections would not terminate. Waiting on the termination of a child process using `wait()` is a blocking operation. A handler for the `SIGCHLD` signal can be set up to asynchronously wait for the termination of child processes and prevent zombie processes.

### **Zombie process**

When a child process created using `fork()` exits and the parent process does not `wait()` for it to collect its termination status, the child becomes a zombie process. The child process is said to be in a zombie state. It is a process whose execution is finished but still has an entry in the system process table. Zombie processes utilize processor resources and thus, it is crucial to prevent or get rid of them or the system will eventually run out of available processes or resources. However, when using event handlers, one thing has to be kept in mind that system calls may get interrupted.

# 1. Synchronous HTTP server and client

It is a basic HTTP server that accepts any kind of client request and responds with a hello world text. Client requests are processed in a loop and a new connection is only handled when the previous one is processed. This is because the `accept()` method blocks until an incoming connection is received.

The client application connects to the server, sends a request to the server and prints the response received to the standard output.

### **Example usage:**

_Terminal 1_

> `python3 ./synchronous-server/simple_http_server.py`

_Terminal 2_

> `python3 ./synchronous-server/simple-client.py`

### **Limitations:**

- It is not capable of serving multiple client requests concurrently. Client request handling is done synchronously and subsequent requests need to wait in the request queue until earlier requests are processed.
- On accepting a client request, the server fetches a fixed amount of data from the request only once and reads it. In conditions where the client sends more data than the receive data buffer, the server will fail to read all the data.

# 2. Multi-connection HTTP server using python's selectors module

An HTTP server that is capable of handling multiple client requests simultaneously. This is achieved using the `selectors` module of python that allows checking for I/O completion (reading and/or writing) for more than one socket.

> "This module allows high-level and efficient I/O multiplexing, built upon the select module primitives. Users are encouraged to use this module instead unless they want precise control over the OS-level primitives used.” - [Source](https://docs.python.org/3/library/selectors.html)

The server is capable of receiving all the data sent by the client handling the scenarios where request data is greater than receive buffer.
Thus, it is able to call `send()` and `recv()` as many times as needed.

### **Example usage:**

_Terminal 1_

> `python3 ./multi-connection-server-using-selectors/multi_connection_http_server.py`

_Terminal 2_

> `python3 ./multi-connection-server-using-selectors/client.py --max-conns=2`

### **Limitations:**

- It is not capable of serving multiple client requests concurrently. Client request handling is done synchronously and subsequent requests need to wait in the request queue until earlier requests are processed.

# 3. Concurrent HTTP server and client using `fork()`

An HTTP server that is capable of processing multiple client requests asynchronously as well as concurrently using the `fork()` system call.
The server process, accepts a new client connection, fork a new child process to handle the received client request, and loop again to accept a new client request without waiting for the request processing to be done. Thus, request processing is handled by the child processes. When handling any number of requests, the server ensures zombie processes are not created.

The `wait()` call is a blocking operation and would defeat the purpose of the concurrent server. To overcome this, the server asynchronously waits for the termination status of all the child processes. To achieve this, the server process registers a signal handler for the `SIGCHLD` signal and waits for collecting the termination status of the child processes.

### **Example usage:**

_Terminal 1_

> `python3 ./concurrent-server-using-fork/concurrent_http_server.py`

_Terminal 2_

> `python3 ./concurrent-server-using-fork/client.py --max-clients=5 --max-conns=2`

### **Limitations:**

- On accepting a client request, the server fetches a fixed amount of data from the request only once and reads it (`recv(1024)`). In conditions where the client sends more data than the receive data buffer, the server will fail to read all the data.
