import socket
import os
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
    return cipher.decrypt(ciphertext)


def get_key(file_url):
    with open(file_url, 'rb') as f:
        k = f.read()
    new_key = import_key(k)
    return new_key

class Executer(object):
    def __init__(self,address):
        self.RECEIVE_SIZE = 10240
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(address)
        self.s.recv(self.RECEIVE_SIZE)
        self.public_key_store = {}
        self.private_key_store = {}
        self.username=""
    def process_input(self,inp):
        cmd_lst = inp.split()
        cmd_type, cmd_args = cmd_lst[0],cmd_lst[1:]
        if cmd_type == "reg":
            public_key, private_key = new_keys(2048)
            public_key_export, private_key_export = public_key.exportKey(), private_key.exportKey()
            inp = inp.encode()
            inp += b' '
            inp += public_key_export
            with open(f'keys/private/{cmd_args[0]}.key', 'wb') as f:
                f.write(private_key_export)
            self.s.send(inp)
        elif cmd_type == "send":
            username = cmd_args[0]
            message = ' '.join(cmd_args[1:])
            pub_key = b''
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
            encrypted_msg = encrypt(message.encode(), pub_key)
            send_command = f'send {username} {encrypted_msg}'
            self.s.send(send_command.encode())
        elif cmd_type == 'login':
            cur_username = cmd_args[0]
            self.s.send(inp.encode())
        elif cmd_type == "getMsg":
            if self.username == '':
                return "login first!"
            self.s.send(inp.encode())
            msgs = self.s.recv(self.RECEIVE_SIZE)
            if msgs == b'No message found':
                return msgs
            msg_list = msgs.split(b'[split_msg]')
            if self.username in self.private_key_store:
                priv_key = self.private_key_store[self.username]
            else:
                priv_key = get_key(f'keys/private/{self.username}.key')
                self.private_key_store[self.username] = priv_key

            decrypted_msg_list = []
            for msg in msg_list:
                utf8_raw_encoded = encode(msg[2:-1].decode('unicode_escape'), 'raw_unicode_escape')
                decrypted_msg = decrypt(utf8_raw_encoded, priv_key)
                decrypted_msg_list.append(decrypted_msg)
            return decrypted_msg_list
        else:
            self.s.send(inp.encode())
        resp = self.s.recv(self.RECEIVE_SIZE)
        return resp.decode()