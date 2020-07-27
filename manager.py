import snet, threading, json
from cryptography.fernet import Fernet

serv = snet.ss_serv(2162)

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
            u.secure_send("join"+ user.username + u.random_esc + snet.ss_serv.ul_str())
        except:
            print("fuck")

def action(data):
    global user
    to_do = data
    try:
        to_do = to_do[:4]
    except:
        print("error coorupted")
        to_do = ""
    return to_do

def action_c(data,user):
    content = data
    try:
        content = content[data.find(user.random_esc)+len(user.random_esc):]
    except:
        print("error coorupted data")
        content = ""
    return content

def action_u(data,user):
    username = data
    try:
        username = username[4:data.find(user.random_esc)]
    except:
        print("error coorupted data")
        username = ""
    return username


def wait_recv(user):
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()
            #what to do
            to_do = action(data)
            if to_do == "mesg":
                send_all(to_do,data,user)
            elif to_do == "quit":
                leaved(user)
                send_all(to_do,data,user)
                return
        except:
            user.socket.close()
            leaved(user)
            for u in serv.user_list:
                try:
                    u.secure_send("quit" + user.username + u.random_esc + snet.ss_serv.ul_str())
                except:
                    print("error")
            print("Error with client, certainly closed")
            break

def leaved(user):
    try:
        serv.user_list.pop(serv.user_list.index(user))
    except:
        print("delete failed")


def send_all(act,msg,sender):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send(act + action_u(msg,sender) + u.random_esc + action_c(msg,sender))
        except:
            print("error")


if __name__ == "__main__": #make a console
    listenning()
    



"""
key = Fernet.generate_key()

s = snet.secure_socket(key)

try:
    print(s.t)
except AttributeError as a:
    print(a)
"""