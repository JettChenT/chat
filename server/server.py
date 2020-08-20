import socket
# noinspection PyUnresolvedReferences
from users import UserStore
# noinspection PyUnresolvedReferences
from messages import MessageQueue
# noinspection PyUnresolvedReferences
from alias import aliasStore
from threading import Thread
import json

with open("config.json") as cfg:
    config = json.load(cfg)
    addr = config["server"]["addr"]
    port = config["server"]["port"]


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((addr, port))

addresses = {}
logins = {}
userSt = UserStore()
aliasSt = aliasStore()
MQ = MessageQueue()
def parse_rec(inp, cli):
    cmd_lst = inp.split(" ")
    cmd_type, cmd_args = cmd_lst[0], cmd_lst[1:]
    if cmd_type == "reg":
        rsd = userSt.register(*cmd_args[:2], " ".join(cmd_args[2:]))
        if rsd:
            return "registered!"
        else:
            return "some error occured!"
    elif cmd_type == "login":
        print("logging in...")
        rsd = userSt.login(*cmd_args)
        if rsd:
            logins[cli] = cmd_args[0]
            return "You're logged in!"
        else:
            return "Please enter the correct password or username"
    elif cmd_type == "listUsers":
        return "\n".join(userSt.list_id())
    elif cmd_type == "send":
        username = logins[cli]
        to_user = aliasSt.get_target(username,cmd_args[0])
        if userSt.user_exists(to_user):
            MQ.add_message(to_user, " ".join(cmd_args[1:]))
            return "Message sent!"
        else:
            return "User does not exist."
    elif cmd_type == "getMsg":
        username = logins[cli]
        print(f"getting message for {username}:")
        msg = MQ.get_message(username)
        if msg == None:
            return "No message found"
        return msg
    elif cmd_type == "getPubKey":
        to_alias = cmd_args[0]
        username = logins[cli]
        to_user = aliasSt.get_target(username,to_alias)
        to_user = to_user.decode()
        return userSt.get_pub_key(to_user)
    elif cmd_type == "match":
        username = logins[cli]
        matched_username = userSt.match(username)
        print(username,matched_username)
        alias1,alias2 = aliasSt.store_alias(username, matched_username)
        return f"{alias1}/{alias2}"
    elif cmd_type == "exists":
        return str(userSt.user_exists(*cmd_args))
    elif cmd_type == "offline":
        userSt.set_offline(logins[cli])
    return "Received！"


def recv_inc_conn():
    while True:
        s.listen()
        client, client_address = s.accept()
        print(f"{client_address[0]}:{client_address[1]} has connected!")
        client.send(b"Hello,hello!")
        print(client)
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):
    t = 0
    while True:
        cmd = client.recv(2048).decode()
        print(cmd)
        r = parse_rec(cmd, client)
        if r !="Received！":
            print(r)
        if type(r) == str:
            client.send(r.encode())
        else:
            client.send(r)
        t += 1


if __name__ == "__main__":
    s.listen(20)
    print("Waiting for connection...")
    acc_thread = Thread(target=recv_inc_conn)
    acc_thread.start()
    acc_thread.join()
    s.close()
