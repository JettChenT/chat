import socket
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA512, SHA384, SHA256, SHA, MD5
from Crypto import Random
from codecs import encode
from base64 import b64encode, b64decode

RECEIVE_SIZE = 10240
hash = "SHA-256"

# socket init
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("202.182.119.187", 6000))
s.recv(1024)

# keys storage
public_key_store = {}
private_key_store = {}


# RSA basic functions

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


cur_username = ''

while True:
    inp = input("Enter your command:\n")
    if inp == "exit":
        print("bye")
        break
    cmd_lst = inp.split()
    cmd_type, cmd_args = cmd_lst[0], cmd_lst[1:]
    if cmd_type == "reg":
        public_key, private_key = new_keys(2048)
        public_key_export, private_key_export = public_key.exportKey(), private_key.exportKey()
        inp = inp.encode()
        inp += b' '
        inp += public_key_export
        with open(f'keys/private/{cmd_args[0]}.key', 'wb') as f:
            f.write(private_key_export)
        s.send(inp)
    elif cmd_type == "send":
        username = cmd_args[0]
        message = ' '.join(cmd_args[1:])
        pub_key = b''
        if username in public_key_store:
            pub_key = public_key_store[username]
        elif os.path.exists(f'keys/public/{username}.key'):
            with open(f'keys/public/{username}.key', 'rb') as f:
                pub_key = f.read()
            public_key_store[username] = pub_key
        else:
            s.send(f"getPubKey {username}".encode())
            pub_key = s.recv(RECEIVE_SIZE)
            with open(f'keys/public/{username}.key', 'wb') as f:
                f.write(pub_key)
            public_key_store[username] = pub_key
        pub_key = import_key(pub_key)
        encrypted_msg = encrypt(message.encode(), pub_key)
        send_command = f'send {username} {encrypted_msg}'
        s.send(send_command.encode())
    elif cmd_type == 'login':
        cur_username = cmd_args[0]
        print(f"Username:{cur_username}")
        s.send(inp.encode())
    elif cmd_type == "getMsg":
        if cur_username == '':
            print("login first!")
            continue
        s.send(inp.encode())
        msgs = s.recv(RECEIVE_SIZE)
        if msgs == b'No message found':
            print(msgs)
        msg_list = msgs.split(b'[split_msg]')
        if cur_username in private_key_store:
            priv_key = private_key_store[cur_username]
        else:
            priv_key = get_key(f'keys/private/{cur_username}.key')
            private_key_store[cur_username] = priv_key

        decrypted_msg_list = []
        cnt = 1
        for msg in msg_list:
            utf8_raw_encoded = encode(msg[2:-1].decode('unicode_escape'),'raw_unicode_escape')
            decrypted_msg = decrypt(utf8_raw_encoded, priv_key).decode()
            print(f'{cnt}) {decrypted_msg}')
            decrypted_msg_list.append(decrypted_msg)
            cnt += 1
        continue
    else:
        s.send(inp.encode())
    resp = s.recv(RECEIVE_SIZE)
    print(resp.decode())
