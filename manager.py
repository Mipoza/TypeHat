import snet, threading, json, os
from cryptography.fernet import Fernet

serv = None

def listenning(): 
    serv.listen(10)
    
    while True:
        r = serv.wait_connect()
        if r == True:
            new_user_in(serv.user_list[-1])
            threading.Thread(target=wait_recv,args=[serv.user_list[-1]]).start()
        else:
            continue

def new_user_in(user):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send("join"+ user.username + u.random_esc + snet.ss_serv.ul_str())
        except:
            print("fuck")

def get_action(data):
    global user
    to_do = data
    try:
        to_do = to_do[:4]
    except:
        print("error coorupted")
        to_do = ""
    return to_do

def get_content(data,user):
    content = data
    try:
        content = content[data.find(user.random_esc)+len(user.random_esc):]
    except:
        print("error coorupted data")
        content = ""
    return content

def get_username(data,user):
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
            to_do = get_action(data)
            if to_do == "mesg":
                send_all(to_do,data,user)
            elif to_do == "quit":
                leaved(user)
                return
        except:
            user.socket.close()
            leaved(user)
            print("Error with client, certainly closed")
            break

def leaved(user):
    try:
        serv.user_list.pop(serv.user_list.index(user))
    except:
        print("delete failed")
    
    for u in serv.user_list:
        try:
            u.secure_send("quit" + user.username + u.random_esc + snet.ss_serv.ul_str())
        except:
            print("error")

def send_all(act,msg,sender):
    for u in serv.user_list:
        try:
            u.secure_send(act + get_username(msg,sender) + u.random_esc + get_content(msg,sender))
        except:
            print("error")

if __name__ == "__main__": 
    port = 2101
    password = ""
    started = False

    print("""
    Welcome to Secure Chat Server !
    """)

    while True:
        action = input("> ")

        if action == "start":
            if not started:
                started = True
                serv = snet.ss_serv(port,password) #try
                threading.Thread(target=listenning).start()
                print("Server as started!")
            else:
                print("Server already started.")
        elif action == "exit":
            os._exit(0)
        elif action[:4] == "port":
            try:
                port = int(action[5:])
            except:
                print("This is not a number.")
        elif action[:4] == "pass":
            password = action[5:]
        else:
            print("Unknow command")
    



"""
key = Fernet.generate_key()

s = snet.secure_socket(key)

try:
    print(s.t)
except AttributeError as a:
    print(a)
"""