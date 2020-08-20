import redis
from hashlib import pbkdf2_hmac, sha1
import random
import os


class UserStore(object):
    def __init__(self):
        self.red = redis.Redis(db=1)
        self.sha_iter = 100000
        self.online_users = []

    def register(self, username, password, public_key) -> bool:
        user_id = sha1(username.encode()).hexdigest()
        if self.red.hexists(user_id, "username"):
            return False
        salt = os.urandom(32)
        hsh_pw = pbkdf2_hmac("sha256", password.encode(), salt, self.sha_iter)
        self.red.rpush("users", user_id)
        self.red.hset(user_id, "pw", hsh_pw)
        self.red.hset(user_id, "salt", salt)
        self.red.hset(user_id, "username", username)
        self.red.hset(user_id, "pub_key", public_key)
        self.red.hset(user_id, "online", "False")
        return True

    def get_id(self, username):
        if type(username)==str:
            username = username.encode()
        user_id = sha1(username).hexdigest()
        return user_id

    def login(self, username, password) -> bool:
        if not self.user_exists(username):
            return False
        user_id = self.get_id(username)
        salt = self.red.hget(user_id, "salt")
        correct_pw = self.red.hget(user_id, "pw")
        hsh_pw = pbkdf2_hmac("sha256", password.encode(), salt, self.sha_iter)
        if correct_pw == hsh_pw:
            self.set_online(username)
            return True
        return False

    def set_online(self, username):
        user_id = self.get_id(username)
        self.red.rpush("onlineUsers",user_id)
        self.red.hset(user_id, "online", "True")

    def match(self, username):
        if len(self.online_users)<=1:
            return self.match_offline(username)
            # everyone except user is offline
        return self.match_online(username)


    def match_offline(self,username):
        users = self.list_id()[:]
        users.remove(username)
        return random.choice(users)

    def match_online(self,username):
        users = self.online_users[:]
        if username in users:
            users.remove(username)
        return random.choice(users)

    def set_offline(self, username):
        user_id = self.get_id(username)
        if username in self.online_users:
            self.online_users.remove(username)
            self.red.lrem("onlineUsers", -1, username)
            self.red.hset(user_id, "online", "False")

    def list_id(self) -> list:
        user_id_list = self.red.lrange("users", 0, -1)
        names_list = [self.red.hget(i, "username").decode() for i in user_id_list]
        return names_list

    def user_exists(self, username) -> bool:
        user_id = self.get_id(username)
        if self.red.hexists(user_id, "username"):
            return True
        return False

    def get_pub_key(self, username):
        user_id = self.get_id(username)
        if not self.red.hexists(user_id, "username"):
            return "user does not exist"
        pub_key = self.red.hget(user_id, "pub_key")
        return pub_key
