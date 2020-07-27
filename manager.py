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
            u.secure_send("join"+ user.username + u.random_esc +" has join the chat !")
        except:
            pass #is disconneted ?

def action(data):
    global user
    to_do = data
    try:
        to_do = to_do[:4]
    except:
        print("error coorupted")
    return to_do

def action_c(data,user):
    content = data
    try:
        content = content[data.find(user.random_esc)+len(user.random_esc):]
        
    except:
        print("error coorupted data")
    return content

def action_u(data,user):
    username = data
    try:
        username = username[4:data.find(user.random_esc)]
    except:
        print("error coorupted data")
    return username


def wait_recv(user):
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()
            #what to do
            to_do = action(data)
            if to_do == "mesg":
                send_all(data,user)
        except:
            user.socket.close()
            print("Error with client, certainly closed")
            break

def send_all(msg,sender):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send("mesg" + action_u(msg,sender) + u.random_esc + action_c(msg,sender))
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