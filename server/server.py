import socket
import json
import hashlib
import redis

with open('config.json') as cfg:
    config = json.load(cfg)
    addr = config['server']['addr']
    port = config['server']['port']


s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(addr, port)

red = redis.Redis()

def parse_rec(inp):
    cmd_lst = inp.split()
    cmd_type,cmd_args = cmd_lst[0],cmd_lst[1:]
    if cmd_type == 'reg':
        print('register account!')

while True:
    cmd,addr = s.recvfrom(1024)
    cmd = cmd.decode()
    parse_rec(cmd)
