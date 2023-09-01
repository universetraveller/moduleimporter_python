int_1 = 1
str_1 = '1'
def func1(i):
    return i
def func5(a:int, b:int, c:str, d:list, e:dict):
    return a
class clz:
    def __init__(self, i):
        self.i = i
    def func1(self, i):
        return i
    @classmethod
    def clzm(cls, i):
        return i
import sqlite3
