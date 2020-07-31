from executer import Executer
import copy
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from threading import Thread
from time import sleep
import sys

class LoginForm(QWidget):
    def __init__(self, server_exec):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.server_exec = server_exec
        self.title = "Login/Register"
        self.layout = QGridLayout()
        # initiate tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300,400)
        self.tabs.addTab(self.tab1,"log in")
        self.tabs.addTab(self.tab2,"register")
        # Reused widgets
        layout1 = QGridLayout()
        layout2 = QGridLayout()
        label_login_name = QLabel("<font size='4'> Username </font>")
        label_register_name = QLabel("<font size='4'> Username </font>")
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Please enter your username")
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Please enter your username")
        layout1.addWidget(label_login_name, 0, 0)
        layout1.addWidget(self.login_username, 0, 1)
        layout2.addWidget(label_register_name, 0, 0)
        layout2.addWidget(self.register_username, 0, 1)
        label_login_password = QLabel("<font size='4'> Password </font>")
        label_register_password = QLabel("<font size='4'> Password </font>")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText('Please enter your password')
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText('Please enter your password')
        layout1.addWidget(label_login_password, 1, 0)
        layout1.addWidget(self.login_password, 1, 1)
        layout2.addWidget(label_register_password, 1, 0)
        layout2.addWidget(self.register_password, 1, 1)
        # tab 1
        button_login = QPushButton('login')
        button_login.clicked.connect(self.login)
        layout1.addWidget(button_login, 2, 0, 1, 2)
        self.tab1.setLayout(layout1)
        # tab 2
        button_register = QPushButton('register')
        layout2.addWidget(button_register,2,0,1,2)
        self.tab2.setLayout(layout2)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def login(self):
        r = self.server_exec.exec_(f"login {self.login_username.text()} {self.login_password.text()}")
        msg = QMessageBox()
        msg.setText(r)
        if r == "You're logged in!":
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            self.close()
        else:
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()


class ChatWindow(QWidget):
    def __init__(self, server_exec):
        super(ChatWindow, self).__init__()
        self.server_exec = server_exec
        self.setWindowTitle("Chatty")
        self.loginWindow = LoginForm(self.server_exec)
        self.initUI()
        self.loginWindow.show()
        self.MQ = []

    def initUI(self):
        self.text_area = QTextEdit(self)
        self.text_area.setFocusPolicy(Qt.NoFocus)
        self.message = QLineEdit(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.text_area)
        self.layout.addWidget(self.message)
        self.setLayout(self.layout)
        self.message.returnPressed.connect(self.send_message)
        thread = Thread(target=self.fetch_new_messages, daemon=True)
        thread.start()

    def send_message(self):
        if self.server_exec.not_logged_in():
            print("log in first!")
            self.not_logged_in_popup()
        else:
            self.server_exec.exec_(self.message.text())
            self.message.clear()
            print(f"{self.server_exec.username}:sent!")

    def not_logged_in_popup(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Not logged in!")
        msg.setText("Please log in to send a message")
        msg.setIcon(QMessageBox.Critical)
        x = msg.exec_()

    def display_new_messages(self):
        while len(self.MQ):
            self.text_area.append(self.MQ.pop(0))

    def fetch_new_messages(self):
        while True:
            new_message = self.server_exec.exec_("getMsg")
            if type(new_message) == list:
                for msg in new_message:
                    decoded_msg = msg.decode()
                    print(decoded_msg)
                    self.MQ.append(decoded_msg)
            sleep(0.5)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Chat application")
        self.server_exec = Executer(("202.182.119.187", 6000))
        self.mainWidget = ChatWindow(self.server_exec)
        self.setCentralWidget(self.mainWidget)

def window():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    timer = QTimer()
    timer.timeout.connect(win.mainWidget.display_new_messages)
    timer.start(1000)
    sys.exit(app.exec_())


window()
