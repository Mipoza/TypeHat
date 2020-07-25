import snet, socket, time, threading, os, sys
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListView, QItemDelegate, QStyleOptionViewItem, QStyle, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator

user = None

class connection_box(QDialog):
    def __init__(self):
        super(connection_box, self).__init__()

        #disable hint mark
        flags = self.windowFlags()
        helpFlag = Qt.WindowContextHelpButtonHint
        flags = flags & (~helpFlag)   
        self.setWindowFlags(flags)
        
        self.setWindowTitle("Connection dialog")
        
        self.line_ip = QLineEdit()
        self.line_port = QLineEdit()
        self.line_user = QLineEdit()

        self.connect = QPushButton("Connect")
        self.connect.setEnabled(False)

        self.line_ip .setPlaceholderText("IP address or dns")
        self.line_port.setPlaceholderText("Port number")
        self.line_user.setPlaceholderText("Username")
        
        self.line_port.setValidator(QIntValidator(0, 65536))

        lay = QVBoxLayout()

        lay.addWidget(self.line_ip )
        lay.addWidget(self.line_port)
        lay.addWidget(self.line_user)
        lay.addWidget(self.connect)
        
        self.setLayout(lay)

        self.line_ip .textChanged.connect(lambda:self.check())
        self.line_port.textChanged.connect(lambda:self.check())
        self.line_user.textChanged.connect(lambda:self.check())
        self.connect.clicked.connect(lambda:self.connection())
    
    def connection(self):
        connecting(self.line_ip.text(),int(self.line_port.text()),self.line_user.text())
    
    def check(self):
        if len(self.line_ip.text()) > 0 and len(self.line_port.text()) > 0 and len(self.line_user.text()) > 0:
            self.connect.setEnabled(True)
        else:
            self.connect.setEnabled(False)


       

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

    def add_msg(self, msg):
        if user == None: #tmp, replace with tryexe^ct
            item = message_item("Mipoza: "+msg)
        else:
            item = message_item(user.username+msg)
        self.model.appendRow(item)

class main_window(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(main_window, self).__init__(*args, **kwargs)
        self.setWindowTitle("Secure Chat")

        box = QGroupBox()

        hlay = QVBoxLayout()
        msg_lay = QHBoxLayout()

        self.line_msg = QLineEdit()
        self.line_msg.setPlaceholderText("Enter a message")

        self.send = QPushButton("Send")
        self.send.setEnabled(False)

        self.chat_ui = chat_view()

        msg_lay.addWidget(self.line_msg)
        msg_lay.addWidget(self.send)

        hlay.addWidget(self.chat_ui)
        hlay.addLayout(msg_lay)

        box.setLayout(hlay)

        self.setCentralWidget(box)
        self.resize(600,500)

        self.send.clicked.connect(lambda:self.send_msg())
        self.line_msg.textChanged.connect(lambda:self.check_len())
    
    def send_msg(self):
        self.chat_ui.add_msg(self.line_msg.text())
    
    def check_len(self):
        if len(self.line_msg.text()) > 0:
            self.send.setEnabled(True)
        else:
            self.send.setEnabled(False)

    def keyPressEvent(self, e):
        if e.key()  == Qt.Key_Return:
            self.send.click()



def connecting(host, port, username):
    global user
    
    while True:
        try:
            connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connexion.connect((host, port))
        except:
            print("Cant reach server, retry in 2 seconds...")
            time.sleep(2)
        else:
            break
    
    key = Fernet.generate_key()
    key_RSA = connexion.recv(2048)

    recipient_key = RSA.import_key(key_RSA)
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_session_key = cipher_rsa.encrypt(key)

    connexion.send(enc_session_key)

    user = snet.user(key, connexion, username)

    user.secure_send(username)

    threading.Thread(target=wait_recv,args=[user]).start()

def wait_recv(user):
    while True:
        try:
            data = user.secure_recv() #dont forget later for image
            data = data.decode()
            print(data)
        except:
            user.socket.close()
            print("Error server was closed")
            os._exit(0)



if __name__ == "__main__":
    #username = str(input("Enter an username: "))
    #connecting('127.0.0.1',2012,username)
    
    #send msg, gui etc with PyQt5
    app = QApplication(sys.argv)

    window = main_window()
    window.show()

    msg_box = connection_box()

    msg_box.exec()

    app.exec_()