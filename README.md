# CS 432 - Project 1 - Proxy Server

Note: instructions work with macOS.

# Get Started
`python3 proxy.py 127.0.0.1`

# Test GET
`curl -x 127.0.0.1:8000 -H "Host: example.com" -X GET http://www.example.com/`

# Test POST
`curl -x 127.0.0.1:8000 -d "message=hello world" -H "Host: httpbin.org" -X POST http://httpbin.org/post`

# Test Non-Supported Methods
`curl -x 127.0.0.1:8000 -d "message=hello world" -H "Host: httpbin.org" -X CONNECT http://www.example.com/ --output output.o`
`cat output.o`

# Firefox
Firefox should be able to use this proxy server for http.
