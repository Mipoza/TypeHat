import snet, socket, time, threading, os, sys, json, pyaudio
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QListWidget, QListWidgetItem,  QFileDialog, QAbstractItemView, QLabel, QMainWindow, QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListView, QItemDelegate, QStyleOptionViewItem, QStyle, QDialog
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, pyqtSignal, QThread, QThreadPool, QObject, QSize, QFileInfo, QStandardPaths
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator, QFont, QIcon, QPixmap, QMovie



user = None
scall_user = None
window = None

def size_format(s):
    size = int(s)
    
    prefix = "B"
    length  = len(str(size))

    if length >= 4 and length <= 6:
        prefix = "KB"
        size /= 10**3
    elif length >= 7 and length <= 9:
        prefix = "MB"
        size /= 10**6
    elif length > 9:
        prefix = "GB"
        size /= 10**9

    return (str(round(size,1)),prefix)


def get_action(data):
    global user
    to_do = data
    try:
        to_do = to_do[:4]
    except:
        print("error coorupted data")
        to_do = ""
    return to_do

def get_username(data):
    global user
    username = data
    try:
        username = username[4:data.find(user.random_esc)]
    except:
        print("error coorupted data")
        username = ""
    return username

def get_content(data):
    global user
    content = data
    try:
        content = content[data.find(user.random_esc)+len(user.random_esc):]
    except:
        print("error coorupted data")
        content = ""
    return content

def send_file(usr, data, to_send, file_name):
    usr.secure_send_big(data, to_send, file_name)

def recv_file(user, file_size):
    file_data = user.secure_revc_big(file_size)

    if window.path_file[0] != "":
        f_stream = open(window.path_file[0], "wb")
        f_stream.write(file_data)
        f_stream.close()

def wait_recv_msg(): #separate socket file and image
    global user
    while True:
        try:
            data = user.secure_recv(user.sock_msg) 
            data = data.decode()
            
            to_do = get_action(data)

            if to_do == "mesg":
                window.chat_ui.add_msg(data)
            elif to_do == "join":
                window.chat_ui.join_msg(data)
            elif to_do == "quit":
                window.chat_ui.leave_msg(data)
        except:
            user.sock_msg.close()
            user.sock_file.close()
            print("Error server was closed") #handled graphicly
            os._exit(0) #make it proper

def wait_recv_file(): #separate socket file and image
    global user
    while True:
        try:
            data = user.secure_recv(user.sock_file) 
            data = data.decode()
            
            to_do = get_action(data)

            if to_do == "imag":
                im = user.secure_revc_big(int(get_content(data)))
                window.chat_ui.image_msg(im, get_username(data))
            elif to_do == "file":
                file_size = int(get_content(data))

                window.thread_recv_file.load_state(True)
                recv_file(user, file_size)
                window.thread_recv_file.load_state(False)
            elif to_do == "acpt":
                s = get_content(data)

                size = s[:s.find("/fn/")]
                file_name = s[s.find("/fn/")+4:s.find("/id/")]
                file_id = s[s.find("/id/")+4:]

                window.thread_recv_file.show_box(get_username(data)+" want to send you a file : "+file_name+" "+size_format(size)[0]+size_format(size)[1]+"\n"+"Do you want to accept it ?", file_name)
                
                if window.path_file[0] != "":
                    user.secure_send("acpt" + user.username + user.random_esc + file_id, user.sock_file)
                else:
                    user.secure_send("decl" + user.username + user.random_esc + file_id, user.sock_file)
        except:
            user.sock_msg.close()
            user.sock_file.close()
            print("Error server was closed") #handle it graphicly
            os._exit(0) #make it proper

p = pyaudio.PyAudio()
playing_stream = p.open(format=pyaudio.paInt16, channels=1, rate=44000, output=True, frames_per_buffer=1024) 
recording_stream = p.open(format=pyaudio.paInt16, channels=1, rate=44000, input=True, frames_per_buffer=1024)

def recv_voice():
    global user, scall_user, playing_stream
    while window.in_call:
        try:
            data = scall_user.secure_recvfrom()[0]
            playing_stream.write(data)
        except Exception as e:
            print(e)

def send_voice(host, port):
    global user, scall_user, playing_stream
    while window.in_call:
        try:
            data = recording_stream.read(1024)
            scall_user.secure_sendto(data, (host,port+2))
        except:
            print("UDP call send drop")

def connecting(host, port, username):
    global user, scall_user

    i = 0
    while True: #cancel a 3 times
        try:
            conn_msg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn_msg.connect((host, port))

            conn_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn_file.connect((host, port+1))

            #call_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #call_sock.sendto(b"",(host, port))
        except:
            if i == 3:
                return (False,"attempt")
            time.sleep(0.5)
        else:
            break
        i += 1
    
    

    key = Fernet.generate_key()
    key_RSA = conn_msg.recv(2048)

    try:
        recipient_key = RSA.imporimport_keytKey(key_RSA)
    except:
        recipient_key = RSA.importKey(key_RSA)

    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(key)

    conn_msg.send(enc_session_key)

    user = snet.user(key, conn_msg, conn_file, username)
    #user.sock_call = call_sock

    password = window.line_pass.text()

    user.secure_send(password, conn_msg)
    is_correct = user.secure_recv(conn_msg)
    is_correct = is_correct.decode()


    if is_correct == "1":
        user.secure_send(username + "*/randesc/*" + user.random_esc, conn_msg)

        sameu_and_key = user.secure_recv(conn_msg)
        sameu_and_key = sameu_and_key.decode()
        samer_username = sameu_and_key[0]

        if samer_username == "0":
            scall_user = snet.scall(sameu_and_key[1:])
            scall_user.sock_call.settimeout(1)
            #scall_user.sock_call.bind(("",port+2))
            window.thread_recv_msg.start() #end it with close
            window.thread_recv_file.start()
            return (True,"")
        else:
            return (False,"same")
    else:
        return (False,"pass")
       
class message_item(QStandardItem):
    def __init__(self, text):
        super(message_item, self).__init__(text)
        self.setEditable(False)
        self.setSelectable(False)

class chat_view(QListView):
    def __init__(self):
        super(chat_view, self).__init__()
        self.model = QStandardItemModel(self)
        self.setStyleSheet("QListView::item:hover {background: transparent;}")
        self.setModel(self.model)
        self.list_username = []
        self.setWordWrap(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setIconSize(QSize(550, 550))
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.model.rowsInserted.connect(lambda p:self.scrollToBottom())

    def add_msg(self, msg):
        if user == None: 
            print("user is none")
        else:
            item = message_item(get_username(msg)+" : "+get_content(msg))
            self.model.appendRow(item)
        
    def join_msg(self, msg):
        if user == None: 
            print("user is none")
        else: 
            item = message_item(get_username(msg)+" has joined the chat !")
            self.model.appendRow(item)
        try:
            self.list_username = json.loads(get_content(msg))
        except:
            print("Error with json parse")
        else:
            window.users_list_ui.refresh()

        
    
    def leave_msg(self, msg):
        if user == None: 
            print("user is none")
        else: 
            item = message_item(get_username(msg)+" has leaved the chat !")
            self.model.appendRow(item)

        try:
            self.list_username = json.loads(get_content(msg))
        except:
            print("username not in list")
        else:
            window.users_list_ui.refresh()
        
    def image_msg(self, im, username):
        item = message_item(username+" :")
        self.model.appendRow(item)
        item = message_item("")
        pix = QPixmap()
        pix.loadFromData(im)
        item.setIcon(QIcon(pix))
        self.model.appendRow(item)

class connect_thread(QThread):
    def __init__(self, host, port, username):
        QThread.__init__(self)
        self.host = host
        self.port = port
        self.username =username

    def __del__(self):
        self.wait()

    def run(self):
        self.result = connecting(self.host,self.port,self.username) 

class run_fun(QThread):
    msg_box = pyqtSignal(str, str)
    l_state = pyqtSignal(bool)

    def __init__(self, func, args=[]):
        QThread.__init__(self)
        self.function = func
        self.args = args

    def show_box(self, text, fn):
        self.msg_box.emit(text, fn)

    def load_state(self, b):
        self.l_state.emit(b)

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args)     
    
class users_view(QListView):
    def __init__(self):
        super(users_view, self).__init__()
        self.model = QStandardItemModel(self)
        self.setStyleSheet("QListView::item:hover {background: transparent;}")
        self.setModel(self.model)
        self.setStyleSheet("QListView::item {color: #6a6a6a;}")
        self.setFocusPolicy(Qt.NoFocus)
        self.setIconSize(QSize(18,18))
        self.dict_user_item = {}

    def refresh(self):
        self.model.clear()
        for u in window.chat_ui.list_username:
            item = message_item(u)
            font = item.font()
            font.setPointSize(11)
            #item.setFont(font)
            #item.setIcon(QIcon("../images/incall.png"))
            #self.dict_user_item[]
            self.model.appendRow(item)


class main_window(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(main_window, self).__init__(*args, **kwargs)
        self.setWindowTitle("TypeHat")
        #self.setContentsMargins(10,10,10,10)
        
        #self.thread_recv_msg = threading.Thread(target=wait_recv_msg)
        #self.thread_recv_file = threading.Thread(target=wait_recv_file)
        self.thread_recv_msg = run_fun(wait_recv_msg)
        self.thread_recv_file = run_fun(wait_recv_file)
        self.thread_recv_file.msg_box.connect(lambda t,f: self.show_box_file(t,f), Qt.BlockingQueuedConnection)
        self.thread_recv_file.l_state.connect(lambda b: self.change_loading_file(b), Qt.BlockingQueuedConnection)

        

        self.path_file = ("","")

        #connect
        self.line_ip = QLineEdit("127.0.0.1")
        self.line_port = QLineEdit("2101")
        self.line_user = QLineEdit("Mipoza")
        self.line_pass = QLineEdit()
        self.loading = QLabel()
        self.loading.setVisible(False)

                
        self.line_pass.setEchoMode(QLineEdit.Password)
        self.line_pass.setPlaceholderText("Optionnal")

        self.connect = QPushButton("Connect")
        self.connect.setEnabled(self.line_ip.text() != "")

        w = self.connect.sizeHint().height()

        mv = QMovie("../images/load.gif")
        mv.start()
        mv.setScaledSize(QSize(w,w))
        self.loading.setMovie(mv)
        self.loading.setFixedSize(w,w)

        self.line_ip .setPlaceholderText("IP address or dns")
        self.line_port.setPlaceholderText("Port number")
        self.line_user.setPlaceholderText("Username")
        
        self.line_port.setValidator(QIntValidator(0, 65536))

        con_lay = QHBoxLayout()

        con_lay.addWidget(self.connect)
        con_lay.addWidget(self.loading)

        lay = QVBoxLayout()

        lay.addWidget(self.line_ip )
        lay.addWidget(self.line_port)
        lay.addWidget(self.line_user)
        lay.addWidget(self.line_pass)
        lay.addLayout(con_lay)
        
        self.box_connection = QGroupBox("Connection")
        

        self.box_connection.setLayout(lay)

        self.setCentralWidget(self.box_connection)

        self.line_ip.textChanged.connect(lambda:self.check())
        self.line_port.textChanged.connect(lambda:self.check())
        self.line_user.textChanged.connect(lambda:self.check())
        self.connect.clicked.connect(lambda:self.connection())

        #chat
        
        self.in_call = False
        self.muted = False

        self.box_chat = QGroupBox()
        self.box_chat.setVisible(False)

        hlay = QVBoxLayout()
        msg_lay = QHBoxLayout()
        list_lay = QHBoxLayout()

        self.line_msg = QLineEdit()
        self.line_msg.setPlaceholderText("Enter a message")
        self.send = QPushButton("Send")
        self.send.setEnabled(False)
        self.send_f = QPushButton()
        self.call_but = QPushButton()
        self.mute_but = QPushButton()

        self.mute_but.setVisible(False)

        self.mute_but.setIcon(QIcon("../images/unmute.png"))
        self.call_but.setIcon(QIcon("../images/call.png"))

        self.wait_send = QLabel()
        self.wait_send.setVisible(False)

        wf = self.send_f.sizeHint().height()

        mv_f = QMovie("../images/load.gif")
        mv_f.start()
        mv_f.setScaledSize(QSize(wf,wf))
        self.wait_send.setMovie(mv_f)
        self.wait_send.setFixedSize(wf,wf)

        self.send_f.setIcon(QIcon("../images/add.png"))

        self.chat_ui = chat_view()
        self.users_list_ui = users_view()
        self.users_list_ui.setMaximumWidth(175)

        msg_lay.addWidget(self.mute_but)    
        msg_lay.addWidget(self.call_but)
        msg_lay.addWidget(self.line_msg)
        msg_lay.addWidget(self.send)
        msg_lay.addWidget(self.send_f)
        msg_lay.addWidget(self.wait_send)

        hlay.addWidget(self.chat_ui)
        hlay.addLayout(msg_lay)

        list_lay.addWidget(self.users_list_ui)
        list_lay.addLayout(hlay)
        list_lay.setContentsMargins(13,0,13,13)
        self.box_chat.setLayout(list_lay)

        #self.resize(600,500)

        self.send_f.clicked.connect(lambda:self.send_file())
        self.send.clicked.connect(lambda:self.send_msg())
        self.line_msg.textChanged.connect(lambda:self.check_len())
        self.call_but.clicked.connect(lambda: self.call_manager())
        self.mute_but.clicked.connect(lambda: self.mute_manager())
    
    def connection(self): #make abort
        self.connect.setEnabled(False)
        self.connect.setText("Connection...")
        self.loading.setVisible(True)
        self.my_thread = connect_thread(self.line_ip.text(),int(self.line_port.text()),self.line_user.text())
        self.my_thread.finished.connect(lambda: self.connection_result(self.my_thread.result))
        self.my_thread.start()
        
        #r = connecting()

    def connection_result(self, r):
        if r[0]:
            self.box_connection.setVisible(False)
            self.box_connection.setEnabled(False)
            self.box_chat.setVisible(True)
            self.setCentralWidget(self.box_chat)
            self.resize(650,500)
            self.thread_send_voice = run_fun(send_voice,[self.line_ip.text(),int(self.line_port.text())])
            self.thread_recv_voice = run_fun(recv_voice)
        elif r[1] == "pass":
            self.connect.setEnabled(True)
            self.loading.setVisible(False)
            self.connect.setText("Connect")
            QMessageBox.critical(self, "Error with connection","Wrong password.",QMessageBox.Close)
        elif r[1] == "same":
            self.connect.setEnabled(True)
            self.loading.setVisible(False)
            self.connect.setText("Connect")
            QMessageBox.critical(self, "Error with connection","\""+self.line_user.text()+"\""+" is already used, please change your username.",QMessageBox.Close)
        else:
            self.connect.setEnabled(True)
            self.loading.setVisible(False)
            self.connect.setText("Connect")
            QMessageBox.critical(self, "Error with connection","Server was not found.",QMessageBox.Close)

    def check(self):
        if len(self.line_ip.text()) > 0 and len(self.line_port.text()) > 0 and len(self.line_user.text()) > 0:
            self.connect.setEnabled(True)
        else:
            self.connect.setEnabled(False)
    
    def call_manager(self):
        if not self.in_call:
            self.call_but.setIcon(QIcon("../images/ringoff.png"))
            self.mute_but.setVisible(True)
            self.in_call = True
            self.thread_send_voice.start()
            self.thread_recv_voice.start()
        else:
            self.call_but.setIcon(QIcon("../images/call.png"))
            self.mute_but.setVisible(False)
            self.in_call = False
            self.mute_but.setIcon(QIcon("../images/unmute.png"))
            self.muted = False
            self.thread_send_voice.wait()
            self.thread_recv_voice.wait()

    def mute_manager(self):
        if not self.muted:
            self.mute_but.setIcon(QIcon("../images/mute.png"))
            self.muted = True
        else:
            self.mute_but.setIcon(QIcon("../images/unmute.png"))
            self.muted = False

    def send_msg(self): #real send
        #self.chat_ui.add_msg(self.line_msg.text())
        msg = self.line_msg.text()
        self.line_msg.clear()
        try:
            user.secure_send("mesg"+user.username+user.random_esc+msg, user.sock_msg)
            #self.chat_ui.add_msg(data.decode()) #maybe json for spe carac ?
        except:
            print("Error with socket sending") #print error in red in chat ?

    def change_loading_file(self, enabled):
        self.send_f.setEnabled(not enabled)
        self.wait_send.setVisible(enabled)

    def send_file(self): #new thread
        file_name = QFileDialog.getOpenFileName(self, "Open Image", QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0], "All Files (*.*)")
        #if line_msg.etxt() != "" alors send text and put max size
        if file_name[0] != "":
            try:
                input_f = open(file_name[0],"rb")
                data = input_f.read()
                input_f.close()
            except:
                QMessageBox.critical(self, "File Error","Cant open this file.",QMessageBox.Close)
            else:
                path_and_extension = os.path.splitext(file_name[0])
                extension = path_and_extension[1]
                name = QFileInfo(file_name[0]).fileName() 

                try:
                    if extension in [".png",".jpg",".jpeg",".bmp",".gif",".svg"]: #image (allowed format)
                        to_send = "imag"+user.username+user.random_esc
                        name = ''
                    else: #file
                        to_send = "file"+user.username+user.random_esc

                    self.thread_file = run_fun(send_file,[user,data,to_send,name])
                    self.thread_file.started.connect(lambda: self.change_loading_file(True))
                    self.thread_file.finished.connect(lambda: self.change_loading_file(False))
                    self.thread_file.start()
                except:
                    #QMessageBox.critical(self, "File send Error","An error occured witn file sending.",QMessageBox.Close
                    print("error file sending")
        else:
            pass

    def show_box_file(self, text, f_name):
        r = QMessageBox.question(window, "File sending", text, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        
        if r == QMessageBox.Yes:
            self.path_file = QFileDialog.getSaveFileName(self, "Open Image", QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0]+"/"+f_name, "All Files (*.*)")
        else:
            self.path_file = ("","")

    def check_len(self):
        if len(self.line_msg.text()) > 0 and len(self.line_msg.text()) <= 2000:
            self.send.setEnabled(True)
        else:
            self.send.setEnabled(False)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Return:
            if self.box_chat.isVisible():
                self.send.click()
            else:
                self.connect.click()

    def closeEvent(self,e):
        if user != None:
            try:
                user.secure_send("quit"+user.username+user.random_esc+json.dumps(window.chat_ui.list_username), user.sock_msg)
                user.secure_send("quit"+user.username+user.random_esc, user.sock_file)
            except:
                print("error sending leave")
        os._exit(0) #make proper

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('../images/typehat_ico.png'))
    
    window = main_window()
    window.show()

    app.exec_()


