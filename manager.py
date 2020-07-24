import snet
import threading
from cryptography.fernet import Fernet

serv = snet.ss_serv(2012)

def listenning():
    serv.listen(10)
    while True:
        serv.wait_connect()
        #entered blabla
        #thread for wait message

#make a refresh

if __name__ == "__main__":
    #threading.Thread(target=listenning).start()
    listenning()
    



"""
key = Fernet.generate_key()

s = snet.secure_socket(key)

try:
    print(s.t)
except AttributeError as a:
    print(a)
"""