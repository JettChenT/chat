from executer import Executer
import copy
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from threading import Thread
from time import sleep
from passwordStrength import PasswordStrengthChecker
import sys

class LoginForm(QWidget):
    def __init__(self, server_exec):
        super().__init__()
        self.pwc = PasswordStrengthChecker()
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
        button_register.clicked.connect(self.register)
        layout2.addWidget(button_register,2,0,1,2)
        self.tab2.setLayout(layout2)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def login(self):
        while True:
            r = self.server_exec.exec_(f"login {self.login_username.text()} {self.login_password.text()}")
            if r == False:
                continue
            msg = QMessageBox()
            msg.setText(r)
            if r == "You're logged in!":
                msg.setIcon(QMessageBox.Information)
                msg.exec_()
                self.close()
            else:
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            break

    def register(self):
        is_secure, rsp = self.pwc.is_secure(self.register_password.text())
        if is_secure:
            r = self.server_exec.exec_(f"reg {self.register_username.text()} {self.register_password.text()}")
            msg = QMessageBox()
            msg.setText(r)
            msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(rsp)
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
        self.text_area.setReadOnly(True)
        self.text_area.setAutoFormatting(QTextEdit.AutoAll)
        self.message = QLineEdit(self)
        self.message.setPlaceholderText("Enter your message")
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.text_area,0,0,1,3)
        self.to_user = QLineEdit(self)
        self.to_user.setPlaceholderText("Username")
        self.layout.addWidget(self.to_user,1,0)
        self.layout.addWidget(self.message,1,1)
        self.layout.setColumnStretch(1,3)
        self.layout.setColumnStretch(0,1)
        self.setLayout(self.layout)
        self.message.returnPressed.connect(self.send_message_thread)
        thread = Thread(target=self.fetch_new_messages, daemon=True)
        thread.start()

    def send_message_thread(self):
        sendThread = Thread(target=self.send_message)
        sendThread.start()

    def send_message(self):
        if self.server_exec.not_logged_in():
            print("log in first!")
            self.not_logged_in_popup()
        else:
            html_resp = f"[to <i>{self.to_user.text()}</i>]:{self.message.text()}"
            tc = self.text_area.textCursor()
            form = tc.charFormat()
            form.setForeground(Qt.green)
            tc.setCharFormat(form)
            tc.insertHtml(html_resp)
            self.text_area.append("")
            send_msg = self.message.text()
            self.message.clear()
            self.message.setPlaceholderText("Sending...")
            self.message.setFocusPolicy(Qt.NoFocus)
            while True:
                r = self.server_exec.exec_(f"send {self.to_user.text()} {send_msg}")
                if r == False:
                    print("opps")
                    continue
                self.message.setPlaceholderText("Enter your message")
                self.message.setFocusPolicy(Qt.ClickFocus)
                print(f"{self.server_exec.username}:sent!")
                sleep(0.1)
                break

    def not_logged_in_popup(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Not logged in!")
        msg.setText("Please log in to send a message")
        msg.setIcon(QMessageBox.Critical)
        x = msg.exec_()

    def display_new_messages(self):
        while len(self.MQ):
            self.text_area.textCursor().insertHtml(self.MQ.pop(0))
            self.text_area.append("")

    def fetch_new_messages(self):
        while True:
            try:
                new_message = self.server_exec.exec_("getMsg")
                print(new_message)
                if type(new_message) == list:
                    for msg in new_message:
                        decoded_msg = msg.decode()
                        print(decoded_msg)
                        self.MQ.append(decoded_msg)
                sleep(0.5)
            except:
                continue


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
