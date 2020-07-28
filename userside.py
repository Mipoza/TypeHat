import snet, socket, time, threading, os, sys, json
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtWidgets import QMessageBox, QApplication, QLabel, QMainWindow, QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListView, QItemDelegate, QStyleOptionViewItem, QStyle, QDialog
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, pyqtSignal, QThread, QThreadPool, QObject
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator, QFont, QIcon

user = None
window = None

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

def wait_recv():
    global user
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()

            to_do = get_action(data)

            if to_do == "mesg":
                window.chat_ui.add_msg(data)
            elif to_do == "join":
                window.chat_ui.join_msg(data)
            elif to_do == "quit":
                window.chat_ui.leave_msg(data)
        except:
            user.socket.close()
            print("Error server was closed") #handled graphicly
            os._exit(0)

def connecting(host, port, username):
    global user
    
    i = 0
    while True: #cancel a 3 times
        try:
            connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connexion.connect((host, port))
        except:
            if i == 3:
                return (False,"attempt")
            time.sleep(0.5)
        else:
            break
        i += 1
    
    key = Fernet.generate_key()
    key_RSA = connexion.recv(2048)

    try:
        recipient_key = RSA.imporimport_keytKey(key_RSA)
    except:
        recipient_key = RSA.importKey(key_RSA)

    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(key)

    connexion.send(enc_session_key)

    user = snet.user(key, connexion, username)

    password = window.line_pass.text()

    user.secure_send(password)
    is_correct = user.secure_recv()
    is_correct = is_correct.decode()

    if is_correct == "1":
        user.secure_send(username + "*/randesc/*" + user.random_esc)
        main_window.thread_recv.start() #end it with close
        return (True,"")
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
            item = message_item(get_username(msg)+" has join the chat !")
        try:
            self.list_username = json.loads(get_content(msg))
        except:
            print("Error with json parse")
        else:
            window.users_list_ui.refresh()

        self.model.appendRow(item)
    
    def leave_msg(self, msg):
        if user == None: 
            print("user is none")
        else: 
            item = message_item(get_username(msg)+" has leave the chat !")

        try:
            self.list_username = json.loads(get_content(msg))
        except:
            print("username not in list")
        else:
            window.users_list_ui.refresh()

        self.model.appendRow(item)

class users_view(QListView):
    def __init__(self):
        super(users_view, self).__init__()
        self.model = QStandardItemModel(self)
        self.setStyleSheet("QListView::item:hover {background: transparent;}")
        self.setModel(self.model)
        self.setStyleSheet("QListView::item {color: #6a6a6a;}")
    
    def refresh(self):
        self.model.clear()
        for u in window.chat_ui.list_username:
            item = message_item(u)
            font = item.font()
            font.setPointSize(11)
            item.setFont(font)
            self.model.appendRow(item)


class main_window(QMainWindow):
    thread_recv = threading.Thread(target=wait_recv)
    def __init__(self, *args, **kwargs):
        super(main_window, self).__init__(*args, **kwargs)
        self.setWindowTitle("Secure Chat")
        self.setContentsMargins(10,10,10,10)

        #connect

        self.line_ip = QLineEdit("127.0.0.1")
        self.line_port = QLineEdit("2101")
        self.line_user = QLineEdit("Mipoza")
        self.line_pass = QLineEdit()
        
        self.line_pass.setEchoMode(QLineEdit.Password)
        self.line_pass.setPlaceholderText("Optionnal")

        self.connect = QPushButton("Connect")
        self.connect.setEnabled(self.line_ip.text() != "")

        self.line_ip .setPlaceholderText("IP address or dns")
        self.line_port.setPlaceholderText("Port number")
        self.line_user.setPlaceholderText("Username")
        
        self.line_port.setValidator(QIntValidator(0, 65536))

        lay = QVBoxLayout()

        lay.addWidget(self.line_ip )
        lay.addWidget(self.line_port)
        lay.addWidget(self.line_user)
        lay.addWidget(self.line_pass)
        lay.addWidget(self.connect)
        
        self.box_connection = QGroupBox("Connection")
        

        self.box_connection.setLayout(lay)

        self.setCentralWidget(self.box_connection)

        self.line_ip.textChanged.connect(lambda:self.check())
        self.line_port.textChanged.connect(lambda:self.check())
        self.line_user.textChanged.connect(lambda:self.check())
        self.connect.clicked.connect(lambda:self.connection())

        #chat
        
        self.box_chat = QGroupBox()
        self.box_chat.setVisible(False)

        hlay = QVBoxLayout()
        msg_lay = QHBoxLayout()
        list_lay = QHBoxLayout()

        self.line_msg = QLineEdit()
        self.line_msg.setPlaceholderText("Enter a message")

        self.send = QPushButton("Send")
        self.send.setEnabled(False)

        self.chat_ui = chat_view()
        self.users_list_ui = users_view()
        self.users_list_ui.setMaximumWidth(175)

        msg_lay.addWidget(self.line_msg)
        msg_lay.addWidget(self.send)

        hlay.addWidget(self.chat_ui)
        hlay.addLayout(msg_lay)

        list_lay.addWidget(self.users_list_ui)
        list_lay.addLayout(hlay)

        self.box_chat.setLayout(list_lay)

        #self.resize(600,500)

        self.send.clicked.connect(lambda:self.send_msg())
        self.line_msg.textChanged.connect(lambda:self.check_len())
    
    def connection(self): #make abort
        self.connect.setEnabled(False)
        r = connecting(self.line_ip.text(),int(self.line_port.text()),self.line_user.text())

        if r[0]:
            self.box_connection.setVisible(False)
            self.box_connection.setEnabled(False)
            self.box_chat.setVisible(True)
            self.setCentralWidget(self.box_chat)
            self.resize(650,500)
        elif r[1] == "pass":
            self.connect.setEnabled(True)
            QMessageBox.critical(self, "Error with connection","Wrong password.",QMessageBox.Close)
        else:
            self.connect.setEnabled(True)
            QMessageBox.critical(self, "Error with connection","Server was not found.",QMessageBox.Close)
        
    def check(self):
        if len(self.line_ip.text()) > 0 and len(self.line_port.text()) > 0 and len(self.line_user.text()) > 0:
            self.connect.setEnabled(True)
        else:
            self.connect.setEnabled(False)

    def send_msg(self): #real send
        #self.chat_ui.add_msg(self.line_msg.text())
        msg = self.line_msg.text()
        self.line_msg.clear()
        try:
            user.secure_send("mesg"+user.username+user.random_esc+msg)
            #self.chat_ui.add_msg(data.decode()) #maybe json for spe carac ?
        except:
            print("Error with socket sending") #print error in red in chat ?

    
    def check_len(self):
        if len(self.line_msg.text()) > 0 and len(self.line_msg.text()) <= 2000:
            self.send.setEnabled(True)
        else:
            self.send.setEnabled(False)

    def keyPressEvent(self, e):
        if e.key()  == Qt.Key_Return:
            if self.box_chat.isVisible():
                self.send.click()
            else:
                self.connect.click()

    def closeEvent(self,e):
        if user != None:
            try:
                user.secure_send("quit"+user.username+user.random_esc+json.dumps(window.chat_ui.list_username))
            except:
                print("error sending leave")
        os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = main_window()
    window.show()

    app.exec_()