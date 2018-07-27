"""
Starting place for initial unittest/travis setup
"""
import datetime

def hello_world():
    return 'hello world'

def hello_eric():
    return 'hello eric'


def hello_now():
    d = datetime.datetime.now()
    return 'hello ' + str(d)
