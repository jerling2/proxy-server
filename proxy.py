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
PROXY_PORT = 6060
# Allow maximum of 5 connections to wait in queue.
PROXY_CONNECTION_QUEUE_SIZE = 5

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


# ---------------------------------------------------------------------------- #
# -------------------------------- Main Driver ------------------------------- #

# Create a TCP socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.bind((PROXY_IP, PROXY_PORT))
tcpSerSock.listen(PROXY_CONNECTION_QUEUE_SIZE)
logger.info(f"Proxy listening on {PROXY_IP}:{PROXY_PORT}")

while True:
    client_socket, client_address = tcpSerSock.accept()
    logger.info(f"Connection established from address {client_address}")
    client_socket.send(bytes("Welcome to the server!", "utf-8"))

    # Read "bytes" from socket file
    socket_file = client_socket.makefile('rb', 0)

    # Read and print data from the client
    data = socket_file.read(1024)
    logger.info(data)
    
    # CLose client connection
    socket_file.close()
    client_socket.close()

# Close proxy sever
tcpSerSock.close()
print("proccess halted")