import socket
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class secure_socket:
    def __init__(self, key, socket, buffer=2048):
        self.key = key
        self.encrypter = Fernet(key)
        self.socket = socket
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
            result = self.encrypter.decrypt(self.socket.recv(self.buffer))
        except:
            print("An error occured with send")
        else:
            return result

class Users:
    pass

class ss_serv():
    connection_list = [] #make user class and make this an users list
    def __init__(self, port, buffer=2048):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = buffer
        self.socket.bind(('',self.port))
        self.key_RSA = RSA.generate(2048)
    
    def listen(self, max):
        self.socket.listen(max)
    
    def wait_connect(self):
        try:
            connection, infos = self.socket.accept()
            connection.send(self.key_RSA.publickey().export_key())
            enc_key = connection.recv(self.buffer)

            cipher_rsa = PKCS1_OAEP.new(self.key_RSA)
            self.key = cipher_rsa.decrypt(enc_key)
            ss = secure_socket(self.key, connection, self.buffer)

            connection_list.append(ss)
        except socket.error as err:
            print("error occured for accepting socket : {}".format(err))