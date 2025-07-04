import math as _math

def sqrt(x):
    return _math.sqrt(x)

def pow(x, y):
    return _math.pow(x, y)

def abs(x):
    return _math.fabs(x)

def round(x, ndigits=0):
    return _math.floor(x * (10 ** ndigits) + 0.5) / (10 ** ndigits) if ndigits else round(x)