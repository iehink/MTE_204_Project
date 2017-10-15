#https://noobtuts.com/python/vector
import math

def add(u, v):
    return [a + b for a, b in zip(u,v)]

def sub(u, v):
    return [a - b for a, b in zip(u,v)]

def mag(u):
    return math.sqrt(sum([a ** 2 for a in u]))

def scalarMult(u, m):
    return [a*m for a in u]
