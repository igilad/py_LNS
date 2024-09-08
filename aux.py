def extract_digits(s:str):
    return int(''.join(c for c in s if c.isdigit()))

def bin_to_char(digit):
    map = {0: '.', 1: '@', 2: 'S', 3:'G'}
    return map[digit]