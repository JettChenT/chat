import socket
import os
import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random
from codecs import encode


def new_keys(keysize):
    random_generator = Random.new().read
    key = RSA.generate(keysize, random_generator)
    private, public = key, key.publickey()
    return public, private


def import_key(extern_key):
    return RSA.importKey(extern_key)


def encrypt(msg, pkey):
    cipher = PKCS1_OAEP.new(pkey)
    return cipher.encrypt(msg)


def decrypt(ciphertext, priv_key):
    cipher = PKCS1_OAEP.new(priv_key)
    print(ciphertext)
    return cipher.decrypt(ciphertext)


def get_key(file_url):
    with open(file_url, 'rb') as f:
        k = f.read()
    new_key = import_key(k)
    return new_key


class Executer(object):
    def __init__(self, address, alias_url="alias.json"):
        self.RECEIVE_SIZE = 10240
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(address)
        self.s.recv(self.RECEIVE_SIZE)
        self.alias_url = alias_url
        with open(alias_url,'r') as f:
            self.aliasDict = json.load(f)
        self.public_key_store = {}
        self.private_key_store = {}
        self.send_que = []
        self.check_for_messages=False
        self.executing = False
        self.username = ""

    def store_alias(self,aliasStr):
        alias1,alias2 = aliasStr.split('/')
        self.aliasDict[self.username][alias2] = alias1

    def exec_(self, inp):
        cmd_lst = inp.split()
        print(cmd_lst)
        if self.executing:
            return False
        self.executing = True
        cmd_type, cmd_args = cmd_lst[0], cmd_lst[1:]
        if cmd_type == "getMsg":
            if self.check_for_messages == False:
                self.executing = False
                return b'Not checking for messages...'
            if self.username == '':
                self.executing = False
                return "login first!"
            self.s.send(inp.encode())
            msgs = self.s.recv(self.RECEIVE_SIZE)
            if msgs == b'No message found':
                self.executing = False
                return msgs
            if self.username in self.private_key_store:
                priv_key = self.private_key_store[self.username]
            else:
                priv_key = get_key(f'keys/private/{self.username}.key')
                self.private_key_store[self.username] = priv_key
            decrypted_msg_list=[]
            utf8_raw_encoded = encode(msgs[2:-1].decode('unicode_escape'), 'raw_unicode_escape')
            decrypted_msg = decrypt(utf8_raw_encoded, priv_key)
            pi = 0
            for i in range(len(decrypted_msg)):
                if decrypted_msg[i:i+1] == b']':
                    pi = i
                    break
            sender_alias, my_alias = decrypted_msg[1:pi].split(b':')
            sender_alias, my_alias = map(lambda x: x.decode(),[sender_alias,my_alias])
            print(sender_alias,my_alias)
            if self.username not in self.aliasDict:
                self.aliasDict[self.username] = {}
            self.aliasDict[self.username][sender_alias] = my_alias
            decrypted_msg_list.append(decrypted_msg)
            self.executing = False
            return decrypted_msg_list
        elif cmd_type == "reg":
            public_key, private_key = new_keys(2048)
            public_key_export, private_key_export = public_key.exportKey(), private_key.exportKey()
            inp = inp.encode()
            inp += b' '
            inp += public_key_export
            with open(f'keys/private/{cmd_args[0]}.key', 'wb') as f:
                f.write(private_key_export)
            self.s.send(inp)
        elif cmd_type == "send":
            self.check_for_messages=False
            username = cmd_args[0]
            message = ' '.join(cmd_args[1:])
            if username in self.public_key_store:
                pub_key = self.public_key_store[username]
            elif os.path.exists(f'keys/public/{username}.key'):
                with open(f'keys/public/{username}.key', 'rb') as f:
                    pub_key = f.read()
                self.public_key_store[username] = pub_key
            else:
                self.s.send(f"getPubKey {username}".encode())
                pub_key = self.s.recv(self.RECEIVE_SIZE)
                with open(f'keys/public/{username}.key', 'wb') as f:
                    f.write(pub_key)
                self.public_key_store[username] = pub_key
            pub_key = import_key(pub_key)
            print(self.aliasDict)
            my_alias = self.aliasDict[self.username][username]
            message = f"[{my_alias}:{username}]:"+message
            encrypted_msg = encrypt(message.encode(), pub_key)
            send_command = f'send {username} {encrypted_msg}'
            self.s.send(send_command.encode())
        elif cmd_type == 'login':
            self.s.send(inp.encode())
            resp = self.s.recv(self.RECEIVE_SIZE).decode()
            if resp == "You're logged in!":
                self.username = cmd_args[0]
            self.check_for_messages = True
            self.executing = False
            return resp
        elif cmd_type == 'match':
            self.s.send(inp.encode())
            resp = self.s.recv(self.RECEIVE_SIZE).decode()
            alias1,alias2 = resp.split('/')
            if self.username not in self.aliasDict:
                self.aliasDict[self.username] = {}
            self.aliasDict[self.username][alias1] = alias2
            self.check_for_messages = True
            self.executing = False
            return alias1, alias2
        else:
            self.check_for_messages=False
            self.s.send(inp.encode())
        resp = self.s.recv(self.RECEIVE_SIZE)
        self.check_for_messages=True
        self.executing = False
        return resp.decode()

    def not_logged_in(self) -> bool:
        return self.username==""

    def on_exit(self):
        with open(self.alias_url,'w') as f:
            json.dump(self.aliasDict,f)
        self.s.close()