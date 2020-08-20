import redis
# noinspection PyUnresolvedReferences
from random_name import RandomNameGenerator


class aliasStore(object):
    def __init__(self):
        self.red = redis.Redis(db=2)
        self.random_name_generator = RandomNameGenerator()

    def store_alias(self, user1, user2):
        user1_alias = self.random_name_generator.generate()
        user2_alias = self.random_name_generator.generate()
        self.red.hset(user1, user2_alias, user2)
        self.red.hset(user2, user1_alias, user1)
        return user2_alias, user1_alias

    def remove_alias(self, user, alias):
        self.red.hdel(user, alias)
        self.random_name_generator.delete_name(alias)
        return True

    def get_target(self, user, alias):
        target = self.red.hget(user, alias)
        return target
