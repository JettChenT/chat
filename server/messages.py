import redis
from hashlib import sha1


class MessageQueue(object):
    def __init__(self):
        self.red = redis.Redis()

    def add_message(self, user, msg):
        user_id = sha1(user.encode()).hexdigest()
        self.red.lpush(user_id, msg)
        return True

    def get_message(self, user):
        user_id = sha1(user.encode()).hexdigest()
        return self.red.rpop(user_id)