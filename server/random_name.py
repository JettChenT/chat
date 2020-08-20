import random


class RandomNameGenerator(object):
    def __init__(self):
        with open("animals.txt") as f:
            self.animals = f.readlines()

        with open("adjectives.txt") as f:
            self.adjectives = f.readlines()

        self.generated = []

    def generate(self):
        animal = random.choice(self.animals)
        animal = animal.lower()
        animal = animal.strip("\n")
        adjective = random.choice(self.adjectives)
        adjective = adjective.capitalize()
        adjective = adjective.strip("\n")
        res = f"{adjective}-{animal}"
        if res in self.generated:
            return self.generate()
        self.generated.append(res)
        return res

    def delete_name(self,name):
        self.generated.remove(name)