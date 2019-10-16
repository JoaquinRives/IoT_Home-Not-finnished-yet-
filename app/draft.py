lista = [None, 2, None]

if not all(x is None for x in lista):
    print(1)
else:
    print(0)
