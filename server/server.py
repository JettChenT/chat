import socket
from users import userStore
from threading import Thread
import json

with open('config.json') as cfg:
    config = json.load(cfg)
    addr = config['server']['addr']
    port = config['server']['port']


s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((addr, port))

addresses = {}
userSt = userStore()
def parse_rec(inp):
    cmd_lst = inp.split()
    cmd_type,cmd_args = cmd_lst[0],cmd_lst[1:]
    if cmd_type == 'reg':
        rsd = userSt.register(*cmd_args)
        if rsd:
            return "registered!"
        else:
            return "some error occured!"
    elif cmd_type=='login':
        print("logging in...")
        rsd = userSt.login(*cmd_args)
        if rsd:
            return "You're logged in!"
        else:
            return "Please enter the correct password or username"
    return "Received！"


def recv_inc_conn():
    while True:
        s.listen()
        client,client_address = s.accept()
        print(f'{client_address[0]}:{client_address[1]} has connected!')
        client.send(b'Hello,hello!')
        addresses[client] = client_address
        Thread(target=handle_client,args=(client,)).start()

def handle_client(client):
    t = 0
    while True:
        cmd = client.recv(1024).decode()
        print(cmd)
        r = parse_rec(cmd)
        print(r)
        client.send(r.encode())
        t+=1

if __name__ == "__main__":
    s.listen(20)
    print("Waiting for connection...")
    acc_thread = Thread(target=recv_inc_conn)
    acc_thread.start()
    acc_thread.join()
    s.close()