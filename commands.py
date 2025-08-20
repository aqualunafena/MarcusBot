import random

def random_chance(chance):
    threshold = 1 - chance
    probability = random.random()
    if probability >= threshold:
        return True
    else:
        return False