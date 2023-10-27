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
from urllib.parse import urlparse

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

    def __connect_to_target(cls):
        cls.target_socket = socket(AF_INET, SOCK_STREAM)
        cls.target_socket.connect((cls.target_host, 80))

    def __close_target_socket(cls):
        cls.target_socket.close()

    def __write_socket_file(cls):
        cls.target_socket_file = cls.target_socket.makefile('rwb', 0)
        msg = "GET  " + "http://" + cls.target_filename + "HTTP/1.0\n\n"
        msg = msg.encode('utf-8')
        cls.target_socket_file.write(msg)

    def __accept(cls):
        return cls.socket.accept()

    def wait_for_connection(cls):
        cls.client_socket, cls.client_address = cls.__accept()
        logger.info(f"Connection established from address {cls.client_address}")
    
    def wait_for_response(cls):
        msg = cls.client_socket.recv(SOCKET_FILE_BUFFER_SIZE)
        return msg.decode('utf-8')

    def wait_for_socket_file(cls, client_or_server: str):
        if client_or_server == 'from client':
            cls.client_socket_file = cls.client_socket.makefile('rb', 0)
        if client_or_server == 'from web server':
            cls.target_socket_file = cls.target_socket.makefile('rb', 0)
    
    def create_socket_file_data_dict(cls, client_or_server: str):
        if client_or_server == 'from client':
            socket_file = cls.client_socket_file
        elif client_or_server == 'from web server':
            socket_file = cls.target_socket_file

        data_dict = dict()

        # Extract the Request Line
        request_line = socket_file.readline(SOCKET_FILE_BUFFER_SIZE).decode('utf-8').split()
        data_dict['method'] = request_line[0]
        data_dict['url'] = request_line[1]
        data_dict['version'] = request_line[2]

        # Extract the Headers
        while True:
            line = socket_file.readline(SOCKET_FILE_BUFFER_SIZE)
            line = line.decode('utf-8').strip()
            if not line:
                # Reached end of headers
                break
            header, value = line.split(':', 1)
            data_dict[header] = value
        
        # Extract the Body
        body = ""
        while True:
            line = socket_file.readline(SOCKET_FILE_BUFFER_SIZE)
            line = line.decode('utf-8').strip()
            if not line:
                break
            body += line

        if client_or_server == 'from client':
            cls.client_socket_data_dict = data_dict
        elif client_or_server == 'from web server':
            cls.target_socket_data_dict = data_dict
            cls.target_body = body
    
    def extract_filename(cls):
        target_url = cls.client_socket_data_dict['url']
        
        # Remove any forward backslash
        target_url = target_url.partition("/")[2]

        # seperate url into netloc (domain) and path.
        url_parse = urlparse(target_url)
        target_filename = url_parse.netloc

        # Remove subdomain (such as www.)
        domains = target_filename.split('.')    
        if len(domains) > 2:
            target_host = domains[1] + '.' + domains[2]

        # Extract the port number
        target_port_pos = target_filename.find(":")
        if target_port_pos != -1:
            target_port = int(target_filename[target_port_pos+1:])
        elif url_parse.scheme == 'https':
            target_port = 443
        else:
            target_port = 80
        
        # Add path to filename but remove any trailing backslash.
        target_filename += url_parse.path.rstrip("/")
        
        cls.target_scheme = url_parse.scheme
        cls.target_host = target_host
        cls.target_filename = target_filename
        cls.target_port = target_port

    def check_cache(cls):
        file_exist = False
        try:
            # Check wether the file exist in the cache
            f = open(cls.target_filename, "r")
            outputdata = f.readlines()
            file_exist = True
            for line in outputdata:
                print(line)
            # ProxyServer finds a cache hit and generates a response message
            cls.emit("HTTP/1.0 200 OK\r\n")
            cls.emit("Content-Type:text/html\r\n")
            # Fill in start.
            # Fill in end.
            print('Read from cache')
        
        # Error handling for file not found in cache
        except IOError:
            if file_exist == False:
                # Create a socket on the proxyserver

                # Remove any sub-domains
                print(cls.target_host)
                print(cls.target_scheme)

                cls.__connect_to_target()
                cls.__write_socket_file()
                cls.wait_for_socket_file('from web server')
                cls.create_socket_file_data_dict('from web server')
                f = open(cls.target_filename, "wb")

                f.write(cls.target_body)
               
                # cls.emit(b"HTTP/1.0 200 OK\r\n")
                # cls.emit(b"Content-Type:text/html\r\n")

                # cls.target_socket_file = cls.target_socket.makefile('rwb', 0)
                # msg = "GET  " + "http://" + cls.target_filename + "HTTP/1.0\n\n"
                # msg = msg.encode('utf-8')
                # cls.target_socket_file.write(msg)


                # tempSocketFile = cls.client_socket.makefile('rwb', 0)
                # response = "HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\nHello, World!"
                # tempSocketFile.send(response.encode('utf-8'))
                # # try:
                    # Connect to the socket to port 80
                    # # Fill in start.
                    # # Fill in end.
                    
                    # # Create a temporary file on this socket and ask port 80 for the file requested by the client
                    # fileobj = c.makefile('r', 0)
                    # fileobj.write("GET  " + "http://" + filename + "HTTP/1.0\n\n")
                    # # Read the response into buffer
                    # # Fill in start.
                    # # Fill in end.

                    # # Create a new file in the cache for the requested file.
                    # # Also send the response in the buffer to client socketand the corresponding file in the cache
                    # tmpFile = open("./" + filename,"wb")
                    # # Fill in start.
                    # # Fill in end.
                # except:
                #     print("Illegal request")

            else:
                # HTTP response message for file not found
                # Fill in start.
                # Fill in end.
                pass
            

    def close_client(cls):
        cls.client_socket_file.close()
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
    proxy.client_socket.recv(1000)
    # proxy.emit("Ready to serve...")

    # proxy.wait_for_socket_file('from client')

    # proxy.client_socket.recv(1000)
    socket_file = proxy.client_socket.makefile('rwb', 0)
    response = b'HTTP/1.0 200 OK\nContent-Type: text/html\n\n'
    body = b"""<html><body><h1>Hello World</h1> this is my server!</body></html>"""
    proxy.client_socket.send(response)
    proxy.client_socket.send(body)
    # proxy.create_socket_file_data_dict('from client')
    # proxy.extract_filename()
    # proxy.check_cache()
    # response = """HTTP/1.1 200 OK\r\nContent-Length: text/html\r\n\r\n"""
    # html_content = proxy.target_body
    

    # proxy.client_socket.send((response + html_content).encode('utf-8'))
    # proxy.close_client()
    
proxy.close()