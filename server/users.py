import redis
from hashlib import pbkdf2_hmac,sha1
import os

class userStore(object):
    def __init__(self):
        self.red = redis.Redis(db=1)
        self.sha_iter = 100000
    def register(self, username, password, public_key):
        user_id = sha1(username.encode()).hexdigest()
        if self.red.hexists(user_id,'username'):
            return False
        salt = os.urandom(32)
        hsh_pw = pbkdf2_hmac('sha256', password.encode(), salt, self.sha_iter)
        self.red.rpush('users',user_id)
        self.red.hset(user_id,'pw',hsh_pw)
        self.red.hset(user_id,'salt',salt)
        self.red.hset(user_id, 'username', username)
        self.red.hset(user_id,'pub_key',public_key)
        return True
    def login(self,username,password):
        user_id = sha1(username.encode()).hexdigest()
        salt = self.red.hget(user_id,'salt')
        correct_pw = self.red.hget(user_id,'pw')
        hsh_pw = pbkdf2_hmac('sha256', password.encode(), salt, self.sha_iter)
        return correct_pw == hsh_pw