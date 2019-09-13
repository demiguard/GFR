from threading import Timer
from random import randint

def hello():
    print("hello, world")
    #r = randint(0.0, 5.0)
    #print(f", chose r={r}")
    t = Timer(0.1, hello)
    t.start()

t = Timer(0.1, hello)
t.start()  # after 30 seconds, "hello, world" will be printed
