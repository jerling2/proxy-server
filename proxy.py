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

    def resolve(cls):
        """ Loads all data within the class"""
        cls.__extract()
        cls.__cache()

    def respond(cls):
        """ Sends contents to the client """
        pass

    def __extract(cls):
        data = cls.req.decode('utf-8')
        # Split Up HTTP Request
        headers, body = data.split('\r\n\r\n', 1)
        request_line, *header_lines = headers.split('\r\n')
        method, path, version = request_line.split()
        url_parsed = urlparse(path.lstrip('/'))
        # Store data in a dictionary
        cls.req_dict = dict()
        cls.req_dict['method'] = method
        cls.req_dict['path'] = url_parsed.path # note I am using URL parsed path!
        cls.req_dict['version'] = version
        cls.req_dict['scheme'] = url_parsed.scheme
        cls.req_dict['body'] = body
        for header in header_lines:
            key, value = header.split(':', 1)
            cls.req_dict[key.strip()] = value.strip()
        cls.req_dict['domain'] =  url_parsed.netloc

        cache_path = url_parsed.netloc + url_parsed.path
        cache_path = cache_path.rstrip('/')
        cache_path = cache_path.replace('/', '-')
        cls.req_dict['cache_path'] = cache_path

        domains = url_parsed.netloc.split('.')
        if len(domains) > 2:
            cls.req_dict['hostn'] = domains[1] + '.' + domains[2]
        else:
            cls.req_dict['hostn'] = domains[0] + '.' + domains[1]

    def __cache(cls):
        try:
            # Cache hit
            cls.req_file = cls.__read_cache()
            return
        except IOError:
            # Cache miss
            # Temporary connect to web server socket
            c = cls.__http_connect()
            cls.__http_get_request(c)
            req_file = c.makefile('rb', 0)
            # Close the socket when we're done.
            c.close()
            # Write the response to the cache.
            cls.__write_cache(req_file)
            cls.req_file = req_file

    def __http_connect(cls) -> 'socket':
        """Conencts two sockets together. Strictly HTTP."""
        c = socket(AF_INET, SOCK_STREAM)
        c.connect((cls.req_dict['hostn'], 80))
        return c
    
    def __http_get_request(cls, connection):
        request =  f"GET {cls.req_dict['path']} {cls.req_dict['version']}\r\n"
        request += f"Host: {cls.req_dict['domain']}\r\n"
        request += "Connection: close\r\n\r\n" # Specifiy non-persistant connection.
        connection.send(request.encode('utf-8'))
    
    def __read_cache(cls):
        cache_data = b''
        f = open(cls.req_dict['cache_path'], 'rb')
        lines = f.readlines()
        for line in lines:
            cache_data += line
        f.close()
        return cache_data

    def __write_cache(cls, message):
        f = open(cls.req_dict['domain'], 'wb')
        while True:
            data = message.read(BUFFER_SIZE)
            if not data:
                break
            f.write(data)
        f.write(b'\r\n\r\n') # Fail safe to make sure the message has an end.
        f.close()

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