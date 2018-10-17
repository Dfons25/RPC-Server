import serverRPC


def div(*vars):
    result = int(vars[0])
    for elements in vars[1:]:
        result = result / elements
    return result


def add(x,y):
    return x+y


server = serverRPC.ServerManager('127.0.0.1', int('8000'),add,div)