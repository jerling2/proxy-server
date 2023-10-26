"""
    Title: Proxy.py
    Brief: A simple proxy server
    Author: Joseph.
"""

# ---------------------------------------------------------------------------- #
# ------------------------- Standard Library Imports ------------------------- #

from socket import *  # Access to TCP sockets 
import sys  # Access for argv and argc.
import logging  # More flexibile print statements.

# ---------------------------------------------------------------------------- #
# ------------------------------ Global Variable ----------------------------- #

# Hosting proxy server on local host on port 6060
PROXY_IP = '127.0.0.1'
PROXY_PORT = 8000
# Allow maximum of 5 connections to wait in queue.
PROXY_CONNECTION_QUEUE_SIZE = 5
SOCKET_FILE_BUFFER_SIZE = 1024

# ---------------------------------------------------------------------------- #
# ------------------------------- Logger Config ------------------------------ #

# Standard-out Configs.
OUTPUT_STDOUT = True
STDOUT_LEVEL = logging.INFO

# Logfile Configs (for debugging).
OUTPUT_FILE = True
FILENAME = 'logfile.log'
FILE_LEVEL = logging.DEBUG
INDENT_1 = '|   '
INDENT_2 = '|-->'

# ---------------------------------------------------------------------------- #
# -------------------------------- Make Logger ------------------------------- #

# Create Logging Instance.
logger = logging.getLogger(__name__)
# Allow logger's handlers to use DEBUG or higher logs.
logger.setLevel(logging.DEBUG) 

if OUTPUT_STDOUT:
    # Create stream handler.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(STDOUT_LEVEL)

    # Create formatter.
    formatter = logging.Formatter('%(message)s')
    stream_handler.setFormatter(formatter)

    # Add file handler to logger.
    logger.addHandler(stream_handler)

if OUTPUT_FILE:
    # Create file handler.
    file_handler = logging.FileHandler(FILENAME, mode='w')
    file_handler.setLevel(FILE_LEVEL)

    # Create formatter.
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)

    # Add file handler to logger.
    logger.addHandler(file_handler)

# ---------------------------------------------------------------------------- #
# -------------------------------- Exceptions -------------------------------- #

# class UnderflowError(Exception):
#     pass

# class OutOfBoundsError(Exception):
#     pass

# ---------------------------------------------------------------------------- #
# ---------------------------------- Classes --------------------------------- #

class TCPSocket:
    # Singleton Pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
            cls.socket = socket(AF_INET, SOCK_STREAM)
            if 'name' in kwargs:
                cls.name = kwargs['name']
            else:
                cls.name = 'host'
        return cls.instance
    
    def open(cls):
        cls.socket = socket(AF_INET, SOCK_STREAM)
        cls.socket.bind((PROXY_IP, PROXY_PORT))
        cls.socket.listen(PROXY_CONNECTION_QUEUE_SIZE)
        logger.info(f"{cls.name} listening on {PROXY_IP}:{PROXY_PORT}")
        return cls.socket

    def connect(cls, ip, port):
        cls.client_socket = socket(AF_INET, SOCK_STREAM)
        cls.client_socket.connect((ip, port))

    def make_socket_file(cls):
        cls.socket_file = cls.socket.makefile('rwb')

    def write(cls, msg):
        cls.socket_file.write(msg.encode('utf-8'))
        cls.socket_file.flush()

    def __accept(cls):
        return cls.socket.accept()

    def on_connect(cls):
        cls.client_socket, cls.client_address = cls.__accept()
        logger.info(f"Connection established from address {cls.client_address}")
        return True
    
    def wait_for_response(cls):
        msg = cls.client_socket.recv(SOCKET_FILE_BUFFER_SIZE)
        return msg.decode('utf-8')

    def wait_for_socket_file(cls):
        cls.cli_socket_file = cls.client_socket.makefile('rb', 0)
        return True

    def get_socket_file_data(cls):
        return cls.cli_socket_file.read(SOCKET_FILE_BUFFER_SIZE)
        
    def close_client(cls):
        cls.client_socket.close()

    def close_client_socket_file(cls):
        cls.client_socket_file.close()

    def close(cls):
        logger.info(f"{cls.name} closed.")
        cls.socket.close()

    def emit(cls, msg: str):
        cls.client_socket.send(msg.encode('utf-8'))

# ---------------------------------------------------------------------------- #
# -------------------------------- Main Driver ------------------------------- #

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

PROXY_IP = sys.argv[1]

proxy = TCPSocket(name='Proxy')
proxy.open()

while True:
    if proxy.on_connect():
        proxy.emit("Ready to serve...")
        proxy.wait_for_socket_file()
        print(proxy.get_socket_file_data())
        # response = proxy.wait_for_response()
        # print(f'Client: {response}')
    proxy.close_client()

proxy.close()