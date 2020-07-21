import redis
from hashlib import pbkdf2_hmac, sha1
import os


class userStore(object):
    def __init__(self):
        self.red = redis.Redis(db=1)
        self.sha_iter = 100000

    def register(self, username, password, public_key)->bool:
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
        return True

    def login(self, username, password)->bool:
        user_id = sha1(username.encode()).hexdigest()
        salt = self.red.hget(user_id, "salt")
        correct_pw = self.red.hget(user_id, "pw")
        hsh_pw = pbkdf2_hmac("sha256", password.encode(), salt, self.sha_iter)
        return correct_pw == hsh_pw

    def list_id(self)->list:
        user_id_list = self.red.lrange('users',0,-1)
        namesList = [self.red.hget(i,"username").decode() for i in user_id_list]
        return namesList

    def user_exists(self,username)->bool:
        user_id = sha1(username.encode()).hexdigest()
        if self.red.hexists(user_id, "username"):
            return True
        return False

    def get_pub_key(self, username):
        user_id = sha1(username.encode()).hexdigest()
        if not self.red.hexists(user_id, "username"):
            return 'user does not exist'
        pub_key = self.red.hget(user_id,'pub_key')
        return pub_key

