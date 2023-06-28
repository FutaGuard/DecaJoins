from string import ascii_lowercase, digits
import random


def randomstr(length=10):
    """
    Generates a random string of length 10.
    """
    randomlist = digits + ascii_lowercase
    return ''.join(
        [
            randomlist[int(36 * random.random())]
            for i in range(length)
        ]
    )