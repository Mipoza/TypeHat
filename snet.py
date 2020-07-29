import socket, random, string, os, json, time
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class secure_socket:
    def __init__(self, key, socket, buffer=4096):
        self.key = key
        self.encrypter = Fernet(key)
        self.socket = socket
        self.buffer = buffer
    
    def secure_send(self, data):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()
        return self.socket.send(self.encrypter.encrypt(to_send))


    def secure_recv(self):
        return self.encrypter.decrypt(self.socket.recv(self.buffer))

    def secure_send_big(self, data, action):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()

        encrypted_data = self.encrypter.encrypt(to_send)
        size = len(encrypted_data)

        self.secure_send(action+str(size))
        time.sleep(0.2)

        return self.socket.send(encrypted_data)

    def secure_revc_big(self, buffer):
        data = b""
        while len(data) < buffer:
            data += self.socket.recv(buffer)

        return self.encrypter.decrypt(data)


class user(secure_socket):
    def __init__(self, key, connection, username, buffer=4096):
        secure_socket.__init__(self, key, connection, buffer)
        self.username = username
        self.random_esc = ''.join(random.choice(string.ascii_letters+string.digits) for i in range(32))

class ss_serv(): #
    user_list = [] #make user class and make this an users list
    def __init__(self, port, password="", buffer=4096):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = buffer
        self.socket.bind(("",self.port))
        self.password = password
        self.key_RSA = RSA.generate(2048)
    
    def listen(self, max):
        self.socket.listen(max)
    
    
    def ul_str():
        l = []
        for u in ss_serv.user_list: #try ?
            l.append(u.username)
        
        return json.dumps(l)
    
    def wait_connect(self):
        try:
            connection, infos = self.socket.accept()

            try:
                rsa_pub = self.key_RSA.publickey().export_key()
            except:
                rsa_pub = self.key_RSA.publickey().exportKey()

            connection.send(rsa_pub) #for new Crypto use .export_key()
            enc_key = connection.recv(self.buffer)
            
            cipher_rsa = PKCS1_OAEP.new(self.key_RSA)
            self.key = cipher_rsa.decrypt(enc_key)

            new_user = user(self.key, connection, "",self.buffer)

            #here at user recv

            password = new_user.secure_recv()
            password = password.decode()

            if password == self.password:
                new_user.secure_send("1")
                usernameandrand = new_user.secure_recv()
                usernameandrand = usernameandrand.decode()

                try:
                    username = usernameandrand[:(usernameandrand.find("*/randesc/*"))]
                    rand = usernameandrand[(usernameandrand.find("*/randesc/*")+11):]
                except:
                    print("Error no escp, may be security brech, closing")
                    os._exit(0)

                new_user.username = username
                new_user.random_esc = rand

                ss_serv.user_list.append(new_user)
                return True
            else:
                new_user.secure_send("0")
                return False
        except socket.error as err:
            print("error occured for accepting socket : {}".format(err))