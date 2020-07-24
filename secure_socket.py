import socket
from cryptography.fernet import Fernet

class secure_socket:
    def __init__(self, key, encrypte, buffer=1024):
        self.key = key
        self.encrypter = encrypter(key)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = buffer
    
    def secure_send(self, data):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()
        try:
            result = self.socket.send(self.encrypter.encrypt(to_send))
        except:
            print("An error occured with send")
        else:
            return result

    def secure_recv(self):
        try:
            result = self.encrypt.decrypt(self.socket.recv(self.buffer))
        except:
            print("An error occured with send")
        else:
            return result