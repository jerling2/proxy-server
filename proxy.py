"""
    Title: Proxy.py
    Brief: A simple proxy server
    Author: Joseph.
"""

# ---------------------------------------------------------------------------- #
# ------------------------- Standard Library Imports ------------------------- #

from socket import *  # Access to TCP sockets 
import sys  # Access for argv and argc.

# ---------------------------------------------------------------------------- #
# ------------------------------ Global Variable ----------------------------- #

# Hosting proxy server on local host on port 6060
PROXY_IP = '127.0.0.1'
PROXY_PORT = 8000
# Allow maximum of 0 connections to wait in queue.
PROXY_CONNECTION_QUEUE_SIZE = 0
BUFFER_SIZE = 1024

# ---------------------------------------------------------------------------- #
# -------------------------------- TCP SOCKET -------------------------------- #

class TCPSocket:
    # Singleton Pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
            # --- Interface ---
            cls.socket = None
            cls.client_socket = None
            cls.client_address = None
            cls.req = None
            cls.req_dict = None
            cls.res_file = None
            cls.payload = None
        return cls.instance

    def close(cls):
        cls.socket.close()
        print('proxy server closed')

    def close_client(cls):
        cls.client_socket.close()
        print(f'closed {cls.client_address}')

    def open(cls):
        cls.socket = socket(AF_INET, SOCK_STREAM)
        cls.socket.bind((PROXY_IP, PROXY_PORT))
        cls.socket.listen(PROXY_CONNECTION_QUEUE_SIZE)
        print(f'proxy server listening on {PROXY_IP}:{PROXY_PORT}')
        return cls.socket

    def on_connect(cls):
        cls.client_socket, cls.client_address = cls.socket.accept()
        print(f'{cls.client_address[0]}:{cls.client_address[1]} connected')

    def on_request(cls):
        cls.req = cls.client_socket.recv(BUFFER_SIZE)
        print(f"Received request:\n{cls.req}\n\n")

    def validate(cls):
        if cls.req == b'':
            print('broken pipeline... dropping client')
            return False
        return True

    def resolve(cls):
        """ Loads all data within the class"""
        cls.__extract()
        cls.__check_cache()

    def respond(cls):
        """ Sends contents to the client """
        cls.client_socket.send(cls.res_file)

    def reset(cls):
        """ Call after response()"""
        cls.payload = None
        cls.client_socket = None
        cls.client_address = None
        cls.req = None
        cls.req_dict = None
        cls.res_file = None

    def __extract(cls):
        # data = cls.req.decode('utf-8')
        # Split Up HTTP Request
        headers, cls.payload = cls.req.split(b'\r\n\r\n', 1)
    
        # Headers should human-readiable
        headers = headers.decode('utf-8')

        request_line, *header_lines = headers.split('\r\n')
        method, path, version = request_line.split()
        # Store data in a dictionary
        cls.req_dict = dict()
        for header in header_lines:
            key, value = header.split(':', 1)
            cls.req_dict[key.strip()] = value.strip()
        cls.req_dict['method'] = method
       
        host = cls.req_dict.get('Host')
        if host:
            cls.last_host = host
        else:
            cls.host = cls.last_host   

        rel_path_index = path.find(host) + len(host)
        rel_path = path[rel_path_index:]
        cls.req_dict['path'] = rel_path
        cache_path = host + rel_path
        cache_path = cache_path.replace('/', '-').rstrip('-')
        cls.req_dict['cache_path'] = cache_path

    def __check_cache(cls):
        if cls.req_dict['method'] == 'POST':
            cls.__cache_miss()
            return
        try: 
            cls.res_file = cls.__read_cache()
        except IOError:
            cls.__cache_miss()

    def __cache_miss(cls):
        # Cache miss
        # Temporary connect to web server socket
        c = cls.__http_connect()
        cls.__http_request(c)
        res_file = c.makefile('rb', 0)
        # Close the socket when we're done.
        c.close()
        # Write the response to the cache.
        cls.__write_cache(res_file)
        cls.res_file = cls.__read_cache()

    def __http_connect(cls) -> 'socket':
        """Conencts two sockets together. Strictly HTTP."""
        c = socket(AF_INET, SOCK_STREAM)
        c.connect((cls.req_dict['Host'], 80))
        return c
    
    def __http_request(cls, connection):
        request =  f"{cls.req_dict['method']} {cls.req_dict['path']} HTTP/1.0\r\n"
        request += f"Host: {cls.req_dict['Host']}\r\n"
        request += "Connection: close\r\n" # Specifiy non-persistant connection.
        for header, value in cls.req_dict.items():
            if header not in {'method', 'path', 'cache_path', 'Host', 'Connection'}:
                request += f"{header}: {value}\r\n"
       
        request += '\r\n' # End Headers
        request = request.encode('utf-8')
        
        print(f'TEST\n\npayload = {cls.payload}\n\n')

        if cls.payload is not None:
            request += cls.payload
            print(f'received payload {cls.payload}')
            request += b'\r\n\r\n' # End message
        
        connection.send(request)

    def __read_cache(cls):
        cache_data = b''
        f = open(cls.req_dict['cache_path'], 'rb')
        lines = f.readlines()
        for line in lines:
            cache_data += line
        f.close()
        return cache_data

    def __write_cache(cls, message):
        f = open(cls.req_dict['cache_path'], 'wb')
        while True:
            line = message.readline()
            if not line:
                break
            f.write(line)
        f.write(b'\r\n\r\n') # Fail safe to make sure the message has an end.
        f.close()

# ---------------------------------------------------------------------------- #
# -------------------------------- Main Driver ------------------------------- #
def main():
    if len(sys.argv) <= 1:
        print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
        sys.exit(2)

    PROXY_IP = sys.argv[1]

    proxy = TCPSocket()
    proxy.open()
    while True:
        proxy.on_connect()
        proxy.on_request()
        if proxy.validate():
            proxy.resolve()
            proxy.respond()
        proxy.close_client()
        proxy.reset()
    proxy.close()

if __name__ == "__main__":
    main()