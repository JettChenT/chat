import redis
from hashlib import sha1


class MessageQueue(object):
    def __init__(self):
        self.red = redis.Redis()

    def add_message(self, user, msg):
        user_id = sha1(user.encode()).hexdigest()
        self.red.lpush(user_id, msg)
        return True

    def get_messages(self, user):
        user_id = sha1(user.encode()).hexdigest()
        msg_count = self.red.llen(user_id)
        msgs = []
        if msg_count == 0:
            return msgs
        elif msg_count > 5:
            msg_count = 5
        with self.red.pipeline() as pipeline:
            for _ in range(msg_count):
                msgs.append(self.red.lpop(user_id))
            pipeline.execute()
        return msgs
