import socket, random, string, os, json, time
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP



class secure_socket:
    def __init__(self, key, sock_msg, sock_file, buffer=4096):
        self.key = key
        self.encrypter = Fernet(key)
        self.buffer = buffer

        self.sock_msg = sock_msg
        self.sock_file = sock_file
        #self.sock_call = sock_call
    
    def secure_send(self, data, sock):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()
        return sock.send(self.encrypter.encrypt(to_send))


    def secure_recv(self, sock):
        return self.encrypter.decrypt(sock.recv(self.buffer))

    def secure_send_big(self, data, action):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()

        encrypted_data = self.encrypter.encrypt(to_send)
        size = len(encrypted_data)

        self.secure_send(action+str(size), self.sock_file)
        time.sleep(0.2)

        return self.sock_file.send(encrypted_data)

    def secure_revc_big(self, buffer):
        data = b""
        while len(data) < buffer:
            data += self.sock_file.recv(buffer)

        return self.encrypter.decrypt(data)


class user(secure_socket):
    def __init__(self, key, sock_msg, sock_file, username, buffer=4096):
        secure_socket.__init__(self, key, sock_msg, sock_file, buffer)
        self.username = username
        self.random_esc = ''.join(random.choice(string.ascii_letters+string.digits) for i in range(32))

class ss_serv(): 
    def __init__(self, port, password="", buffer=4096):
        self.port = port
        self.buffer = buffer

        self.sock_msg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock_call = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.sock_msg.bind(("",self.port))
        self.sock_file.bind(("",self.port+1))
        #self.sock_call.bind(("",self.port))

        self.password = password
        self.key_RSA = RSA.generate(2048)
        self.user_list = []
    
    def listen(self, max):
        self.sock_msg.listen(max)
        self.sock_file.listen(max)
    
    def ul_str(self):
        l = []
        for u in self.user_list: #try ?
            l.append(u.username)
        
        return json.dumps(l)
    
    def wait_connect(self): #continue
        try:
            conn_msg, infos = self.sock_msg.accept()
            conn_file, infos_file = self.sock_file.accept()

            try:
                rsa_pub = self.key_RSA.publickey().export_key()
            except:
                rsa_pub = self.key_RSA.publickey().exportKey()

            conn_msg.send(rsa_pub) #for new Crypto use .export_key()
            enc_key = conn_msg.recv(self.buffer)
            
            cipher_rsa = PKCS1_OAEP.new(self.key_RSA)
            self.key = cipher_rsa.decrypt(enc_key)

            new_user = user(self.key, conn_msg, conn_file, "", self.buffer)

            #here at user recv

            password = new_user.secure_recv(conn_msg)
            password = password.decode()

            if password == self.password:
                new_user.secure_send("1", conn_msg)
                usernameandrand = new_user.secure_recv(conn_msg)
                usernameandrand = usernameandrand.decode()

                try:
                    username = usernameandrand[:(usernameandrand.find("*/randesc/*"))]
                    rand = usernameandrand[(usernameandrand.find("*/randesc/*")+11):]
                except:
                    print("Error no escp, may be security brech, closing")
                    os._exit(0)

                new_user.username = username
                new_user.random_esc = rand

                self.user_list.append(new_user)
                return True
            else:
                new_user.secure_send("0")
                return False
        except socket.error as err:
            print("error occured for accepting socket : {}".format(err))