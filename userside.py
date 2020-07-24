import snet, socket, time, threading, os
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

user = None

def connecting(host, port, username):
    global user
    
    while True:
        try:
            connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connexion.connect((host, port))
        except:
            print("Cant reach server, retry in 2 seconds...")
            time.sleep(2)
        else:
            break
    
    key = Fernet.generate_key()
    key_RSA = connexion.recv(2048)

    recipient_key = RSA.import_key(key_RSA)
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(key)

    connexion.send(enc_session_key)

    user = snet.user(key, connexion, username)

    user.secure_send(username)

    threading.Thread(target=wait_recv,args=[user]).start()

def wait_recv(user):
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()
            print(data)
        except:
            user.socket.close()
            print("Error server was closed")
            os._exit(0)



if __name__ == "__main__":
    username = str(input("Enter an username: "))
    connecting('127.0.0.1',2012,username)
    #send msg, gui etc with PyQt5