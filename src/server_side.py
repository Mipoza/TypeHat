import snet, threading, json, os, socket, time
from cryptography.fernet import Fernet

serv = None

#make send and recv socket and lock send


def listenning(): 
    serv.listen(10)
    
    while True:
        r = serv.wait_connect()

        if r == True:
            new_user_in(serv.user_list[-1])
            threading.Thread(target=wait_recv_msg,args=[serv.user_list[-1]]).start()
            threading.Thread(target=wait_recv_file,args=[serv.user_list[-1]]).start()
            #threading.Thread(target=wait_recv_call,args=[serv.user_list[-1]]).start() #user for decrypt ?
        else:
            continue

def new_user_in(user):
    for u in serv.user_list: #mb thread for each request ?
        try:
            u.secure_send("join"+ user.username + u.random_esc + serv.ul_str(), u.sock_msg)
        except socket.error as e:
            print(e)
    
    if len(serv.username_in_call) > 0 :
        user.secure_send("ucal" + user.username + user.random_esc + serv.cl_str(), user.sock_file)

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

def call_manager(user, join):
    if join:
        serv.username_in_call.append(user.username)
    else:
        try:
            serv.username_in_call.pop(serv.username_in_call.index(user.username))
        except:
            print("delete voc failed in callm")

    for u in serv.user_list:
        try:
            u.secure_send("ucal" + user.username + u.random_esc + serv.cl_str(), u.sock_msg)
        except:
            print("error")

def wait_recv_msg(user):
    while True:
        try:
            data = user.secure_recv(user.sock_msg) 
            data = data.decode()
            #what to do
            to_do = get_action(data)
            if to_do == "mesg":
                send_all(to_do,data,user)
            elif to_do == "call":
                call_manager(user, True)
            elif to_do == "qcal":
                call_manager(user, False)
            elif to_do == "quit":
                user.sock_msg.close()
                leaved(user)
                return
        except:
            user.sock_msg.close()
            user.sock_file.close()
            leaved(user)
            print("Error with client, certainly closed (msg)")
            break

def wait_recv_file(user):
    while True:
        try:
            data = user.secure_recv(user.sock_file) 
            data = data.decode()

            to_do = get_action(data)
            if to_do == "quit":
                user.sock_file.close()
                return
            elif to_do == "imag":
                send_image(get_content(data,user), user, to_do)
            elif to_do == "file":
                s = get_content(data,user)
                send_file(s[:s.find("/fn/")], s[s.find("/fn/")+4:], user, to_do)
            elif to_do == "decl":
                file_id = int(get_content(data,user))
                f_tuple = serv.fm.get_tuple(file_id)

                if f_tuple != None:
                    try:
                        serv.fm.del_tuple(f_tuple, file_id, user)
                    except:
                        print("error while deleting in file_queue")
            elif to_do == "acpt":
                file_id = int(get_content(data,user))
                f_tuple = serv.fm.get_tuple(file_id)
                
                if f_tuple != None:
                    user.secure_send_big(f_tuple[1], "file"+user.username+user.random_esc)
                    try:
                        serv.fm.del_tuple(f_tuple, file_id, user)
                    except:
                        print("error while deleting in file_queue")

        except:
            #user.sock_msg.close()
            #user.sock_file.close()
            #leaved(user)
            print("Error with client, certainly closed (file)")
            break

def send_vpac(data, addr):
    serv.scall_serv.secure_sendto(data, addr)

def wait_recv_call():
    serv.scall_serv.sock_call.bind(("",serv.port))
    while True:
        try:
            data_and_addr = serv.scall_serv.secure_recvfrom()
            if not (data_and_addr[1] in serv.in_call):
                serv.in_call.append(data_and_addr[1])
            th_list = []

            for addr in serv.in_call:
                if addr != data_and_addr[1]:
                    th_list.append(threading.Thread(target=send_vpac,args=[data_and_addr[0],addr]))
                    th_list[-1].start()

            for t in th_list:
                t.join()

        except Exception as e:
            print(e)
            #break

def leaved(user):
    try:
        serv.user_list.pop(serv.user_list.index(user))
    except:
        print("delete failed")

    try:
        serv.username_in_call.pop(serv.username_in_call.index(user.username))
    except:
        pass
    
    for u in serv.user_list:
        try:
            u.secure_send("quit" + user.username + u.random_esc + serv.ul_str(), u.sock_msg)
        except:
            print("error")

def send_image(size, user, act):
    data = user.secure_revc_big(int(size))

    for u in serv.user_list:
        try:
            u.secure_send_big(data, act + user.username + u.random_esc) #test
        except:
            print("error with file sending")
    
def send_file(size, fn, user, act):
    data = user.secure_revc_big(int(size))

    u_l = []
    for u in serv.user_list:
        if u != user:
            u_l.append(u)
        
    file_id = serv.fm.add_file(data, u_l)
    
    th_list = []

    for u in serv.user_list:
        try:
            if u != user:
                u.secure_send("acpt" + user.username + u.random_esc + size + "/fn/" + fn + "/id/" + str(file_id), u.sock_file)
        except:
            print("error with file sending")

def send_all(act,msg,sender):
    for u in serv.user_list:
        try:
            u.secure_send(act + get_username(msg,sender) + u.random_esc + get_content(msg,sender), u.sock_msg)
        except:
            print("error")

if __name__ == "__main__": 
    port = 2101
    password = ""
    started = False

    print("""
    Welcome to TypeHat Server !
    """)

    while True:
        action = input("> ").lower()

        if action == "start":
            if not started:
                started = True
                serv = snet.ss_serv(port,password) #try
                threading.Thread(target=listenning).start()
                threading.Thread(target=wait_recv_call).start()
                print("Server has started!")
            else:
                print("Server already started.")
        elif action == "exit": #end
            if started:
                for u in serv.user_list:
                    try:
                        u.close()
                    except:
                        print("cannot close client socket")
                serv.sock_msg.close()
                serv.sock_file.close()
            os._exit(0)
        elif action[:4] == "port": #verif range, max-1
            try:
                port = int(action[5:])
            except:
                print("This is not a number.")
        elif action[:4] == "pass":
            password = action[5:]
        else:
            print("Unknow command")
    
