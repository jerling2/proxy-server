"""
    Title: Proxy.py
    Brief: A simple proxy server
    Author: Joseph.
"""

# ---------------------------------------------------------------------------- #
# ------------------------- Standard Library Imports ------------------------- #

from socket import *  # Access to TCP sockets 
import sys  # Access for argv and argc.
from urllib.parse import urlparse

# ---------------------------------------------------------------------------- #
# ------------------------------ Global Variable ----------------------------- #

# Hosting proxy server on local host on port 6060
PROXY_IP = '127.0.0.1'
PROXY_PORT = 8001
# Allow maximum of 5 connections to wait in queue.
PROXY_CONNECTION_QUEUE_SIZE = 5
BUFFER_SIZE = 1024

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
        return cls.instance

    def close(cls):
        cls.socket.close()
        print('proxy server closed')

    def close_client(cls):
        cls.client_socket.close()

    def open(cls):
        cls.socket = socket(AF_INET, SOCK_STREAM)
        cls.socket.bind((PROXY_IP, PROXY_PORT))
        cls.socket.listen(PROXY_CONNECTION_QUEUE_SIZE)
        print(f'proxy server listening on {PROXY_IP}:{PROXY_PORT}')
        return cls.socket

    def on_connect(cls):
        cls.client_socket, cls.client_address = cls.socket.accept()
        print(f'{cls.client_address[0]}:{cls.client_address[1]} connected')
        return cls.socket.accept()

    def on_request(cls):
        cls.req = cls.client_socket.recv(BUFFER_SIZE)
   
    def send_html(cls):
        cls.client_socket.send(b'HTTP/1.1 200 OK\n')
        cls.client_socket.send(b'Content-Type: text/html\n\n')
        cls.client_socket.send(b'<!DOCTYPE html><html>hello, world!</html>')

# ---------------------------------------------------------------------------- #
# -------------------------------- Main Driver ------------------------------- #
if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

PROXY_IP = sys.argv[1]

proxy = TCPSocket()
proxy.open()
while True:
    proxy.on_connect()
    proxy.on_request()
    proxy.resolve()
    proxy.respond()
    proxy.close_client()
proxy.close()