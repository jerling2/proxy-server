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
PROXY_PORT = 8001
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

    def __accept(cls):
        return cls.socket.accept()

    def wait_for_connection(cls):
        cls.client_socket, cls.client_address = cls.__accept()
        logger.info(f"Connection established from address {cls.client_address}")
    
    def wait_for_response(cls):
        msg = cls.client_socket.recv(SOCKET_FILE_BUFFER_SIZE)
        return msg.decode('utf-8')

    def wait_for_socket_file(cls):
        cls.cli_socket_file = cls.client_socket.makefile('rb', 0)

    def get_socket_file_data(cls):
        return cls.cli_socket_file
        # return cls.cli_socket_file.read(SOCKET_FILE_BUFFER_SIZE)
    
    def get_socket_file_data_dict(cls):

        request_line = cls.cli_socket_file.readline(SOCKET_FILE_BUFFER_SIZE)
        print(request_line)
        lines = cls.cli_socket_file.readlines(SOCKET_FILE_BUFFER_SIZE)

        for line in lines:
            print(line.decode('utf-8').strip())

    def close_client(cls):
        cls.cli_socket_file.close()
        cls.client_socket.close()

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
    proxy.wait_for_connection()
    proxy.emit("Ready to serve...")
    proxy.wait_for_socket_file()
    proxy.get_socket_file_data_dict()
    proxy.close_client()

proxy.close()