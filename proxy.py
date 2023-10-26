# Dependencies
from socket import *
import sys

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.connect(("127.0.0.1", 6969))

# Create the TCP socket, bind it to a port, and start listening

# rb = "read bytes" from 0 = "anything". This returns a 'SocketFile'.
socketFile = tcpSerSock.makefile('rb',0)

# # This is an equivalent statement:
# socketFile = tcpSerSock.makefile('r', None)

data = socketFile.read()
print(data)

socketFile.close()
tcpSerSock.close()