# Code to provide vector math functionality
# Code altered from:
# Title: Python Vector
# Author: Noob Tuts
# Date Accessed: 2017-10-15
# Availability: https://noobtuts.com/python/vector

import math

# Vector addition
def add(u, v):
    return [a + b for a, b in zip(u,v)]

# Vector subtraction
def sub(u, v):
    return [a - b for a, b in zip(u,v)]

# Vector magnitude
def mag(u):
    return math.sqrt(sum([a ** 2 for a in u]))

# Scalar multiplication of a vector
def scalarMult(u, m):
    return [a*m for a in u]
