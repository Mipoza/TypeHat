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
        
    def secure_send(self, data, sock):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()
        return sock.send(self.encrypter.encrypt(to_send))


    def secure_recv(self, sock):
        d = sock.recv(self.buffer)
        if d != b'':
            return self.encrypter.decrypt(d)
        else:
            return b''

    def secure_send_big(self, data, action, file_name=''):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()

        encrypted_data = self.encrypter.encrypt(to_send)
        size = len(encrypted_data)

        suffix = ''
        if file_name != '':
            suffix = '/fn/'+file_name

        self.secure_send(action+str(size)+suffix, self.sock_file)
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
    
    def close(self):
        self.sock_msg.close()
        self.sock_file.close()

class scall():
    def __init__(self, key, buffer=4096):
        self.key = key
        self.encrypter = Fernet(self.key)
        self.buffer = buffer
        self.sock_call = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def secure_sendto(self, data, addr):
        to_send = data
        if(type(data) == str):
            to_send = to_send.encode()
        return self.sock_call.sendto(self.encrypter.encrypt(to_send), addr)
    
    def secure_recvfrom(self):
        data, addr = self.sock_call.recvfrom(self.buffer)
        return (self.encrypter.decrypt(data), addr)

class file_manager():
    def __init__(self):
        self.file_queue = []
        self.id = 0
    
    def add_file(self, file, user_lsit):
        dict_user = { user_lsit[i] : False for i in range(0,len(user_lsit)) }
        self.file_queue.append((self.id, file, dict_user))
        self.id += 1
        return self.id-1
    
    def end_file(self, file_id):
        f_tuple = None

        for t in self.file_queue:
            if t[0] == file_id:
                f_tuple = t
                break
        
        del self.file_queue[self.file_queue.index(f_tuple)]

    def get_tuple(self, file_id):
        f_tuple = None

        for t in self.file_queue:
            if t[0] == file_id:
                f_tuple = t
                break
        
        return f_tuple
    
    def del_tuple(self, f_tuple, file_id, user):
        if f_tuple != None:
            self.file_queue[self.file_queue.index(f_tuple)][2][user] = True
            dict_user = self.file_queue[self.file_queue.index(f_tuple)][2]

            if all(x==True for x in dict_user.values()):
                self.end_file(int(file_id))

class ss_serv(): 
    def __init__(self, port, password="", buffer=4096):
        self.port = port
        self.buffer = buffer

        self.sock_msg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_call = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.sock_msg.bind(("",self.port))
        self.sock_file.bind(("",self.port+1))
        #self.sock_call.bind(("",self.port))

        self.password = password
        self.key_RSA = RSA.generate(2048)
        self.user_list = []
        #self.dict_addr = {}
        self.username_in_call = []
        self.in_call = []
        self.fm = file_manager()
        self.scall_serv = scall(Fernet.generate_key())
    def listen(self, max):
        self.sock_msg.listen(max)
        self.sock_file.listen(max)
    
    def ul_str(self):
        l = []
        for u in self.user_list:
            l.append(u.username)
        
        return json.dumps(l)

    def cl_str(self):
        l = []
        for u in self.username_in_call: 
            l.append(u)
        
        return json.dumps(l)
    
    def wait_connect(self): #continue
        try:
            conn_msg, infos = self.sock_msg.accept()
            conn_file, infos_file = self.sock_file.accept()
            #conn_call, addr = self.sock_call.recvfrom(self.buffer)
            #conn not socket

            try:
                rsa_pub = self.key_RSA.publickey().export_key()
            except:
                rsa_pub = self.key_RSA.publickey().exportKey()

            conn_msg.send(rsa_pub) #for new Crypto use .export_key()
            enc_key = conn_msg.recv(self.buffer)
            
            cipher_rsa = PKCS1_OAEP.new(self.key_RSA)
            self.key = cipher_rsa.decrypt(enc_key)

            new_user = user(self.key, conn_msg, conn_file, "", self.buffer) #not a socket conn_call

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
                    print("Error no escp, may be security breach, closing")
                    os._exit(0)
                
                same_usrn = False
                for u in self.user_list:
                    if u.username == username:
                        same_usrn = True
                        break

                if same_usrn:
                    new_user.secure_send("1",conn_msg)
                else:
                    new_user.secure_send(b"0"+self.scall_serv.key,conn_msg)

                    new_user.username = username
                    new_user.random_esc = rand

                    self.user_list.append(new_user)
                    #self.dict_addr[conn_msg] = addr

                    return True
            else:
                new_user.secure_send("0", conn_msg)
                return False
        except socket.error as err:
            print("error occured for accepting socket : {}".format(err))