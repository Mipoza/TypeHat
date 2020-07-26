import snet
import threading
from cryptography.fernet import Fernet

serv = snet.ss_serv(2012)

def listenning():
    serv.listen(10)
    while True:
        serv.wait_connect()
        new_user_in(serv.user_list[-1])
        #entered blabla
        #thread for wait message

#make a refresh

def new_user_in(user):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send(user.username + " has join the chat !")
        except:
            pass #is disconneted ?

def wait_recv(user):
    pass

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