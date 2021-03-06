import snet, socket, time, threading, os, sys, json, pyaudio, select
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtWidgets import QMessageBox, QApplication, QCheckBox, QWidget, QLabel, QListWidget, QStyledItemDelegate, QListWidgetItem,  QFileDialog, QAbstractItemView, QLabel, QMainWindow, QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListView, QItemDelegate, QStyleOptionViewItem, QStyle, QDialog
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, pyqtSignal, QThread, QThreadPool, QObject, QSize, QFileInfo, QStandardPaths, QEvent, QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator, QFont, QIcon, QPixmap, QMovie

#lecture video, selection peripherique audio, build with images, make settings menu (add disco to it), make requierement, close socket at quit
#solve distant udp problem, listen ? (maybe select pb ?), check if connect solve pb

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

    while window.listen:
        try:
            ready = select.select([user.sock_msg], [], [], 2) #mb more than 2 sec for real case
            if ready[0]:
                data = user.secure_recv(user.sock_msg) 
                data = data.decode()

                if data == '':
                    window.thread_recv_file.disconnected()
                    break
                
                to_do = get_action(data)

                if to_do == "mesg":
                    window.chat_ui.add_msg(data)
                elif to_do == "join":
                    window.chat_ui.join_msg(data)
                elif to_do == "ucal":
                    window.users_list_ui.join_call(data)
                elif to_do == "sclo":
                    print("here wtf")
                    window.thread_recv_msg.disconnected()
                    break
                elif to_do == "quit":
                    window.chat_ui.leave_msg(data)
        except Exception as e:
            user.sock_msg.close()
            user.sock_file.close()
            print(e)
            print("Error server was closed (msg)") 
            window.thread_recv_msg.disconnected()
            break
            #os._exit(0) #make it proper

def wait_recv_file(): #separate socket file and image
    global user
    while window.listen:
        try:
            ready = select.select([user.sock_file], [], [], 2) #mb more than 2 sec for real case
            if ready[0]:
                data = user.secure_recv(user.sock_file) 
                data = data.decode()
                
                if data == '':
                    window.thread_recv_file.disconnected()
                    break
                
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
                elif to_do == "ucal":
                    window.users_list_ui.join_call(data)
        except Exception as e:
            user.sock_msg.close()
            user.sock_file.close()
            print(e) #handle it graphicly
            print("Error server was closed (file)") #handle it graphicly
            window.thread_recv_file.disconnected()
            break
            #os._exit(0) #make it proper

def recv_voice():
    global user, scall_user, playing_stream
    while window.in_call:
        try:
            ready = select.select([scall_user.sock_call], [], [], 2) #mb more than 2 sec for real case
            if ready[0]:
                data = scall_user.secure_recv()
                window.playing_stream.write(data)

                free = window.playing_stream.get_write_available()
                if free > window.chunck:
                    tofill = free - window.chunck
                    window.playing_stream.write(chr(0) * tofill)
        except Exception as e:
            print(e)

def send_voice(host, port):
    global user, scall_user, playing_stream
    while window.in_call:
        try:
            if not window.muted:
                data = window.recording_stream.read(window.chunck)
                #scall_user.secure_sendto(data, (host,port))
                scall_user.secure_send(data)
            else: 
                time.sleep(0.01) #for prevent ASLA run underoccured
        except:
            print("UDP call send drop")

def connecting(host, port, username):
    global user, scall_user

    i = 0
    while True: #cancel a 3 times
        try:
            conn_msg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn_msg.settimeout(5)
            conn_msg.connect((host, port))
            conn_msg.settimeout(None)

            conn_file = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn_file.settimeout(5)
            conn_file.connect((host, port+1))
            conn_file.settimeout(None)
        except:
            if i == 3:
                return (False,"attempt")
            time.sleep(0.2)
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
            #scall_user.sock_call.settimeout(1)
            scall_user.sock_call.connect((host,port))
            scall_user.sock_call.setblocking(0)
            window.thread_recv_msg.start() #end it with close
            window.thread_recv_file.start()
            return (True,"")
        else:
            return (False,"same")
    else:
        return (False,"pass")

class MyDelegate(QStyledItemDelegate):
    def __init__(self):
        QStyledItemDelegate.__init__(self) 

    def setModelData(self,editor,model,index):
        pass # no changes are written to model

    def eventFilter(self,editor,event):
        if event.type() == QEvent.KeyPress and event.key() not in (Qt.Key_Control, Qt.Key_C):
            return True
        return QStyledItemDelegate.eventFilter(self, editor, event)

class message_item(QListWidgetItem):
    def __init__(self, text, is_for_image=False):
        super(message_item, self).__init__(text)
        #self.setEditable(False)
        #self.setSelectable(False)
        if is_for_image:
            self.setFlags(Qt.ItemIsEnabled)
        else:
            self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)

class chat_view(QListWidget):
    def __init__(self):
        super(chat_view, self).__init__()
        self.setStyleSheet("QListWidget::item:hover {background: transparent;}")
        self.setStyleSheet("QListWidget::item:selected {}")
        self.list_username = []
        self.setWordWrap(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setIconSize(QSize(550, 550))
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.model().rowsInserted.connect(lambda p:self.scrollToBottom())
        self.setItemDelegate(MyDelegate())


    def add_msg(self, msg):
        if user == None: 
            print("user is none")
        else:
            item = message_item(get_username(msg)+": "+get_content(msg))
            self.insertItem(self.count(), item)
        
    def join_msg(self, msg):
        if user == None: 
            print("user is none")
        else: 
            item = message_item(get_username(msg)+" has joined the chat !")
            self.insertItem(self.count(), item)
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
            self.insertItem(self.count(), item)

        try:
            self.list_username = json.loads(get_content(msg))
        except:
            print("username not in list")
        else:
            window.users_list_ui.refresh()
    
        
    def image_msg(self, im, username):
        item = message_item(username+": ", True)
        self.insertItem(self.count(), item)
        item = message_item("", True)
        pix = QPixmap()
        pix.loadFromData(im)
        item.setIcon(QIcon(pix))
        self.insertItem(self.count(), item)

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
    disconnect = pyqtSignal()

    def __init__(self, func, args=[]):
        QThread.__init__(self)
        self.function = func
        self.args = args

    def show_box(self, text, fn):
        self.msg_box.emit(text, fn)

    def load_state(self, b):
        self.l_state.emit(b)
    
    def disconnected(self):
        self.disconnect.emit()

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args)     
    
class users_view(QListWidget):
    def __init__(self):
        super(users_view, self).__init__()
        self.setStyleSheet("QListWidget::item:hover {background: transparent;}")
        self.setStyleSheet("QListWidget::item {color: #6a6a6a;}")
        self.setFocusPolicy(Qt.NoFocus)
        self.setIconSize(QSize(18,18))
        self.in_call = []
    
    def join_call(self, u_call_list):
        self.in_call = json.loads(get_content(u_call_list))
        self.refresh()

    def refresh(self):
        self.clear()
        for u in window.chat_ui.list_username:
            item = message_item(u)
            font = item.font()
            font.setPointSize(11)
            item.setFont(font)
            if u in self.in_call:
                item.setIcon(QIcon("../images/incall.png"))
            self.insertItem(self.count(), item)

class main_window(QMainWindow): #wait for reclick on ring out
    def __init__(self, *args, **kwargs):
        super(main_window, self).__init__(*args, **kwargs)
        self.setWindowTitle("TypeHat")
        #self.setContentsMargins(10,10,10,10)

        self.settings = QSettings("TypeHat","TypeHat")

        self.disconnect_called = False
        self.listen = True
        self.is_closing = False

        self.chunck = 1024
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=41000, output=True, frames_per_buffer=self.chunck) 
        self.recording_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=41000, input=True, frames_per_buffer=self.chunck)
        
        #self.thread_recv_msg = threading.Thread(target=wait_recv_msg)
        #self.thread_recv_file = threading.Thread(target=wait_recv_file)
        self.thread_recv_msg = run_fun(wait_recv_msg)
        self.thread_recv_file = run_fun(wait_recv_file)
        self.thread_recv_file.msg_box.connect(lambda t,f: self.show_box_file(t,f), Qt.BlockingQueuedConnection)
        self.thread_recv_file.l_state.connect(lambda b: self.change_loading_file(b), Qt.BlockingQueuedConnection)

        self.thread_recv_msg.disconnect.connect(lambda : self.disconnect_and_reaload())
        self.thread_recv_file.disconnect.connect(lambda : self.disconnect_and_reaload())

        self.thread_send_voice = None
        self.thread_recv_voice = None

        self.path_file = ("","")

        #connect
        self.init_connection()
        #chat
        self.init_chat()

        self.setCentralWidget(self.main_wid)
    
    def init_connection(self):
        infos = self.load_settings()

        self.line_ip = QLineEdit(infos[0])
        self.line_port = QLineEdit(infos[1])
        self.line_user = QLineEdit(infos[2])
        self.line_pass = QLineEdit()
        self.loading = QLabel()
        self.loading.setVisible(False)
        self.remember = QCheckBox("Remember this server")
        self.remember.setChecked(infos != ("","",""))

        self.logo = QLabel()
        pix = QPixmap("../images/typehat_logo.png")
        pix = pix.scaled(QSize(250,250), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo.setPixmap(pix)
                
        self.line_pass.setEchoMode(QLineEdit.Password)
        self.line_pass.setPlaceholderText("Password")

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
        
        self.line_port.setValidator(QIntValidator(0, 65535))

        con_lay = QHBoxLayout()

        con_lay.addWidget(self.connect)
        con_lay.addWidget(self.loading)

        lay = QVBoxLayout()


        lay.addWidget(self.line_ip)
        lay.addWidget(self.line_port)
        lay.addWidget(self.line_user)
        lay.addWidget(self.line_pass)
        lay.addWidget(self.remember)
        lay.addLayout(con_lay)
        
        self.box_connection = QGroupBox("Connection")

        self.box_connection.setLayout(lay)

        self.main_wid = QWidget()

        m_lay = QVBoxLayout()

        m_lay.addWidget(self.logo)
        m_lay.addWidget(self.box_connection)

        self.main_wid.setLayout(m_lay)

        self.line_ip.textChanged.connect(lambda:self.check())
        self.line_port.textChanged.connect(lambda:self.check())
        self.line_user.textChanged.connect(lambda:self.check())
        self.connect.clicked.connect(lambda:self.connection())

    def init_chat(self):
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

    def load_settings(self):
        ip = str(self.settings.value("host",""))
        port = str(self.settings.value("port",""))
        username = str(self.settings.value("username",""))

        return (ip, port, username)

    def save_settings(self, host, port, username):
        self.settings.setValue("host",host)
        self.settings.setValue("port",port)
        self.settings.setValue("username",username)
        
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
            self.main_wid.setVisible(False)
            self.box_chat.setVisible(True)
            self.setCentralWidget(self.box_chat)
            self.resize(650,500)
            self.thread_send_voice = run_fun(send_voice,[self.line_ip.text(),int(self.line_port.text())])
            self.thread_recv_voice = run_fun(recv_voice)
            if self.remember.isChecked():
                self.save_settings(self.line_ip.text(),self.line_port.text(),self.line_user.text())
            else:
                self.save_settings("","","")
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
            user.secure_send("call"+user.username+user.random_esc, user.sock_msg)
            self.call_but.setIcon(QIcon("../images/ringoff.png"))
            self.mute_but.setVisible(True)
            self.in_call = True
            self.thread_send_voice.start()
            self.thread_recv_voice.start()
        else:
            user.secure_send("qcal"+user.username+user.random_esc, user.sock_msg)
            self.call_but.setIcon(QIcon("../images/call.png"))
            self.mute_but.setVisible(False)
            self.in_call = False
            self.mute_but.setIcon(QIcon("../images/unmute.png"))
            self.muted = False
            self.setEnabled(False)
            self.thread_send_voice.wait()
            self.thread_recv_voice.wait()
            self.setEnabled(True)

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
        except:
            print("Error with socket sending") #if faiiled, disconnect ?

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

    def disconnect_and_reaload(self):
        if not self.disconnect_called and not self.is_closing:
            self.disconnect_called = True
            self.wait_for_threads()
            
            self.box_chat.setVisible(False)
            self.init_connection()
            self.init_chat()
            self.setCentralWidget(self.main_wid)
            self.resize(self.main_wid.sizeHint())
            

            QMessageBox.critical(self, "Error with server","Server was certainly closed.", QMessageBox.Close)
            self.disconnect_called = False
            self.listen = True

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

    def wait_for_threads(self):
        self.listen = False
        self.in_call = False
        self.thread_recv_file.wait()
        self.thread_recv_msg.wait()
        if self.thread_send_voice != None and self.thread_recv_voice != None:
            self.thread_send_voice.wait()
            self.thread_recv_voice.wait()

    def closeEvent(self,e):
        self.is_closing = True
        if user != None:
            try:
                user.secure_send("quit"+user.username+user.random_esc, user.sock_msg)
                user.secure_send("quit"+user.username+user.random_esc, user.sock_file)
            except:
                pass
            self.wait_for_threads()

        #os._exit(0) #make proper

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('../images/typehat_ico.png'))
    
    window = main_window()
    window.show()

    app.exec_()


