import snet
import threading
from cryptography.fernet import Fernet

serv = snet.ss_serv(2050)

def listenning():
    serv.listen(10)
    while True:
        serv.wait_connect()
        new_user_in(serv.user_list[-1])
        threading.Thread(target=wait_recv,args=[serv.user_list[-1]]).start()
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
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()
            send_all(data)
        except:
            user.socket.close()
            print("Error with client, certainly closed")
            break

def send_all(msg):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send(u.username + " " + msg)
        except:
            print("error")


if __name__ == "__main__":
    listenning()
    



"""
key = Fernet.generate_key()

s = snet.secure_socket(key)

try:
    print(s.t)
except AttributeError as a:
    print(a)
"""