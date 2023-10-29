"""
    Title: Proxy.py
    Brief: A simple proxy server capable of GET and POST requests.
    Author: Joseph.
"""

# ---------------------------------------------------------------------------- #
# ------------------------- Standard Library Imports ------------------------- #

from socket import *  # Access to TCP sockets 
import sys  # Access for argv and argc.

# ---------------------------------------------------------------------------- #
# ------------------------------ Global Variable ----------------------------- #

# Hosting proxy server on local host on port 6060
PROXY_IP = '127.0.0.1'  #< (default)
PROXY_PORT = 8000
BUFFER_SIZE = 1024 
# Allow maximum of 5 connections to wait in queue. 
PROXY_CONNECTION_QUEUE_SIZE = 5 # (honestly I don't know what this does)

# ---------------------------------------------------------------------------- #
# -------------------------------- TCP SOCKET -------------------------------- #

class TCPSocket:
    # Singleton Pattern
    def __new__(cls, *args, **kwargs):
        """
        Brief: TCPSocket class defines the TCP socket for the proxy server.
        Design: TCPSocket is a singleton object, meaning no more than one
                instance of a TCPSocket can exist. I chose this design
                because I knew I only want the proxy server to have one socket
                open at any given time.
        Class Variables:
            cls.socket - The proxy's socket object.
            cls.client - The connected client's socket (i.e. browser/end-system)
            cls.req    - The client's request sent to the proxy server.
            cls.req_dict - A dictionary containing header information of cls.req.
            cls.last_host - The last host to have been defined in a client request.
            cls.payload  - The content/body/payload of the client's request.
            cls.res_file - The response file that will be sent back to the client.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
            # --- Variables --- #
            cls.socket = None
            cls.client_socket = None
            cls.client_address = None
            cls.req = None
            cls.req_dict = None
            cls.last_host
            cls.payload = None
            cls.res_file = None
        return cls.instance

    def open(cls):
        """ Open the proxy server so it can be ready to serve."""
        cls.socket = socket(AF_INET, SOCK_STREAM)
        cls.socket.bind((PROXY_IP, PROXY_PORT))
        cls.socket.listen(PROXY_CONNECTION_QUEUE_SIZE)
        print(f'proxy server listening on {PROXY_IP}:{PROXY_PORT}')
        return cls.socket

    def close(cls):
        """ Close the proxy server."""
        cls.socket.close()
        print('proxy server closed')

    def close_client(cls):
        """ Terminate connection between proxy and client."""
        cls.client_socket.close()
        print(f'closed {cls.client_address}')

    def on_connect(cls):
        """ 
        Brief: Wait for a client to connect to proxy. 
        Note:  This function is blocking and will only terminate 
               once a client connects to the proxy.
        """
        cls.client_socket, cls.client_address = cls.socket.accept()
        print(f'{cls.client_address[0]}:{cls.client_address[1]} connected')

    def on_request(cls):
        """ 
        Brief: Wait for a request from the client.
        Usage: on_request() should be called after on_connect(). 
        Note:  This function is blocking and will only terminate 
               once a request is received from the client.
        """
        cls.req = cls.client_socket.recv(BUFFER_SIZE)

    def validate(cls) -> bool:
        """ Simple check whether or not the client's request is empty."""
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
        """ Just to be safe ... """
        cls.payload = None
        cls.client_socket = None
        cls.client_address = None
        cls.req = None
        cls.req_dict = None
        cls.res_file = None

    def __extract(cls):
        """
        Brief: __extract() takes the client's request (cls.req) and splits it
               into the header and payload. Futhermore, __extract() takes out
               the request line from the headers (method, path, and version),
               and loads all the headers into the cls.req_dict.
               Also, __extract() will load the last host defined in a cls.req
               to cls.last_host. This is incase a second request comes in
               without a host header, we can deduce it probably is going to
               the previous host. 
               Lastly, __extract() creates a cache_path, where cache path is:
                'cache_path = 'host name' + 'relative path to file'
        Usage: __extract() should be called after on_request().
        Modifies: cls.req_dict and cls.last_host.
        """
        # Split client's request into headers and payload.
        headers, cls.payload = cls.req.split(b'\r\n\r\n', 1)
        # Headers are human readiable and can be decoded.
        headers = headers.decode('utf-8')
        # Extract request line (method, path, and version).
        request_line, *header_lines = headers.split('\r\n')
        method, path, version = request_line.split()
        # Load headers into the 'request dictionary'.
        cls.req_dict = dict()
        for header in header_lines:
            key, value = header.split(':', 1)
            cls.req_dict[key.strip()] = value.strip()
        cls.req_dict['method'] = method
        # If host is not defined, define it as the last host.
        host = cls.req_dict.get('Host')
        if host:
            cls.last_host = host
        else:
            host = cls.last_host
            cls.req_dict['Host'] = host
        # It is easier if we load the rel-path, not the abs-path.
        rel_path_index = path.find(host) + len(host)
        rel_path = path[rel_path_index:]
        cls.req_dict['path'] = rel_path
        # Create a 'cache path' used as a filename for the cache.
        cache_path = host + rel_path
        cache_path = cache_path.replace('/', '-').rstrip('-')
        cls.req_dict['cache_path'] = cache_path

    def __check_cache(cls):
        """
        Brief: __check_cache() will attempt to check the cache for
               the requested file. However, __check_cache will not
               check the cache for any POST requests. Furthermore,
               __check_cache() will load a 405 error into the 
               cls.res_file if the client is using a method that is 
               not GET or POST.
        Usuage: __check_cache() should be called after __extract().
        Modifes: cls.res_file.
        """
        if cls.req_dict['method'] not in {"GET", "POST"}:
            cls.res_file = cls.__method_not_allowed_err()
            return
        if cls.req_dict['method'] == 'POST':
            cls.__cache_miss()
            return
        try: 
            cls.res_file = cls.__read_cache()
        except IOError:
            cls.__cache_miss()

    def __cache_miss(cls):
        """
        Brief: __cache_miss() is called when we need to contact the server for
               the client's requested file (aka. if the file is not in the cache,
               or if the client sent a POST request).
        Proccess: 1. Set up a temporary socket connection with the server.
                  2. Send the client's request to the server.
                  3. Store server's response in a socket file.
                  4. Close the temporary socket connection with the server.
                  5. Write the socket_file to the cache.               
        Modfies: cls.res_file and the cache (the system's files).
        """
        c = cls.__http_connect()
        cls.__http_request(c)
        socket_file = c.makefile('rb', 0)
        c.close()
        cls.__write_cache(socket_file)
        cls.res_file = cls.__read_cache()

    def __http_connect(cls) -> 'socket':
        """ Connect to server's socket (Strict HTTP only)"""
        c = socket(AF_INET, SOCK_STREAM)
        c.connect((cls.req_dict['Host'], 80))
        return c

    def __http_request(cls, connection):
        """
        Brief: In short, __http_request relays the client's request to the server.
               There are some added details: 1) we specify HTTP/1.0, 2) we specify
               'Connection: close'. Other than that, __http_request follows the
               standard protocol to form the http request.
        Usuage: Used by __check_miss().
        """
        # Headers Start
        request =  f"{cls.req_dict['method']} {cls.req_dict['path']} HTTP/1.0\r\n"
        request += f"Host: {cls.req_dict['Host']}\r\n"
        request += "Connection: close\r\n" # Specifiy non-persistant connection.
        for header, value in cls.req_dict.items():
            if header not in {'method', 'path', 'cache_path', 'Host', 'Connection'}:
                request += f"{header}: {value}\r\n"
        request += '\r\n' 
        request = request.encode('utf-8')
        # -- Headers End
        # (Optional) Payload/Body/Content Start
        if cls.payload is not None:
            request += cls.payload
            print(f'received payload {cls.payload}')
            request += b'\r\n\r\n'
        # -- Payload/Body/Content End
        connection.send(request)

    def __read_cache(cls) -> bytes:
        """
        Brief: Read cache attempts to read the cache file from the cache.
        Return: The binary cache data. This is usally the http response
                given by the server.
        """
        cache_data = b''
        f = open(cls.req_dict['cache_path'], 'rb')
        lines = f.readlines()
        for line in lines:
            cache_data += line
        f.close()
        return cache_data

    def __write_cache(cls, message):
        """
        Brief: Write the server's http response into the cache.
        Usage: __write_cache() is used by __cache_miss().
        """
        f = open(cls.req_dict['cache_path'], 'wb')
        while True:
            line = message.readline()
            if not line:
                break
            f.write(line)
        f.write(b'\r\n\r\n') # Fail safe to make sure the message has an end.
        f.close()
    
    def __method_not_allowed_err(cls) -> bytes:
        """ 405 message stating the client's method is not allowed. """
        error =  "HTTP/1.0 405 Method Not Allowed\r\n"
        error += "Content-Type: text/plain\r\n"
        error += "Content-Length: 21\r\n"
        error += "\r\n"
        error += f"Method is not allowed\r\n\r\n"
        return error.encode('utf-8')

# ---------------------------------------------------------------------------- #
# -------------------------------- Main Driver ------------------------------- #
def main():
    """
    Brief: Opens the proxy server and makes it ready to serve its clients. 
    The Loop: 1. Proxy waits for a client's connection
              2. Proxy receives request from the client
              3. Proxy resolves the request (i.e retrieving the file from the cache or server)
              4. Proxy responds with the requested file (i.e the response file)
              5. Proxy closes its connection with the client (because we're running HTTP/1.0)
              6. Repeat
    """
    if len(sys.argv) <= 1:
        print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
        sys.exit(2)

    global PROXY_IP; PROXY_IP = sys.argv[1]

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