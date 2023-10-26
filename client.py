from socket import *

tcpCliSock = socket(AF_INET, SOCK_STREAM)
tcpCliSock.connect(('127.0.0.1', 6060))

# message = tcpCliSock.recv(2048)


# Create a socket file from the client socket
client_file = tcpCliSock.makefile('rwb')

# Write data to the server
message = "Hello, server!"
client_file.write(message.encode('utf-8'))
client_file.flush()

tcpCliSock.close()
# print(f"Message received: {message.decode('utf-8')}")