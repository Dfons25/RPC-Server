import asyncore
import socket
import threading
import json

insideFuncs = ['pigMaker', 'mult', 'sub']
newFuncs = {}

# Classe responsável gestão do servidor:
#     Inicialização do servidor numa thread
#     Armazenamento das funções disponiveis ao cliente

class ServerManager():

# Input: endereço do servidor, porta do servidor, funções exteriores a serem registadas
# Contexto: É criado o ciclo sobre o qual o servidor irá executar até haver um /exit por parte do utilizador

    def __init__(self, host, port, *outFunctions):
        self.extractFunctions(outFunctions)
        self.cmd = None
        self.status = None
        while (self.cmd != '/exit'):
            try:
                if (self.status == None):
                    self.server = Server(host, port)
                    self.loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
                    self.loop_thread.daemon = True
                    self.loop_thread.start()
                    self.server.listen(5)
                    self.status = 'active'
                self.cmd = input("> ")
            except:
                import traceback
                traceback.print_exc()
                print("Error starting server")

            if (self.cmd == '/ping'):
                x = 5
                while (x > 0):
                    print(x)
                    x = x - 1

# Input: Lista de funções provenientes do input de inicialização da classe
# Contexto: A lista de funções é adicionada a um dicionário com o valor da chave equivalente ao nome da funçõão designada {"nomeDaFunção" : nomeDaFunção}

    def extractFunctions(self, functionList):
        global newFuncs
        for elements in functionList:
            newFuncs.update({str(elements.__name__ ) : elements})

# Input: Tuplo de elementos com os valores recebidos do cliente
# Output: Resultado conseguido com base no input

    def sub(self, vars):
        result = int(vars[0])
        for elements in vars[1:]:
            result -= elements
        return result

# Input: Tuplo de elementos com os valores recebidos do cliente
# Output: Resultado conseguido com base no input

    def mult(self, vars):
        result = 1
        for elements in vars:
            result *= elements
        return result

# Input: Tuplo de elementos com os valores recebidos do cliente
# Output: Resultado conseguido com base no input
# Contexto: Como o tuplo terá apenas um primeiro elemento, a frase a ser trabalhada, é atribuido a "sentence" o valor do primeiro elemento do tuplo
#           Em alternativa, poderia existir um ciclo semelhante à funções anteriores para ser trabalhado "um tuplo de frases", a não existência do mesmo é intencional

    def pigMaker(self, str):
        sentence = str[0]
        print(sentence)
        endings = ['sh', 'gl', 'ch', 'ph', 'tr', 'br', 'fr', 'bl', 'gr', 'st', 'sl', 'cl', 'pl', 'fl']
        sentence = sentence.split()
        for k in range(len(sentence)):
            word = sentence[k]
            if word[0] in ['a', 'e', 'i', 'o', 'u']:
                sentence[k] = word + 'ay'
            elif self.splitter(word) in endings:
                sentence[k] = word[2:] + word[:2] + 'ay'
            elif not word.isalpha():
                sentence[k] = word
            else:
                sentence[k] = word[1:] + word[0] + 'ay'
        return ' '.join(sentence)


# Input: Recebe um string correspondente a uma palavra na frase
# Output: Devolve as duas primeiras letras da palavra

    def splitter(self, str):
        return str[0] + str[1]

# Input: Recebe o resultado a ser enviado ao cliente e o ID do pedido correspondente
# Output: Devolve o valores em formato json

    def jsonMaker(self, result, id):
        return json.dumps({"id": id, "jsonrpc": "2.0", "result": result})

# Input: Json recebido pelo cliente
# Output: Tuplo com os valores existentes nos parametros

    def parametersExtract(self, json):
        joiner = []
        for x in json["params"]:
            joiner.append(x)
        return tuple(joiner)

# Input: Opção correspondente à função a ser utilizada; Variaveis a serem utilizadas como argumentos na função
# Output: Resultado retornado pela função
# Contexto: (Ver explicação do ponto anterior)

    def funcoes(self, opt, vars):
        try:
            if opt == 'sub':
                return self.sub(vars),
            elif opt == 'pigMaker':
                return self.pigMaker(vars)
            elif opt == 'mult':
                return self.mult(vars),
            elif opt == 'welcome':
                return self.giveWelcome()
            else:
                exec('a = self.' + opt + str(vars))
                return locals()['a']
        except:
            #import traceback
            #traceback.print_exc()
            return "error"

# Input: Opção correspondente à função a ser utilizada
# Output: Resultado retornado pela função
# Contexto: Caso na função a acima a função não seja encontrada dentro da classe, a mesma será redirecionada para aqui, para ser então chamada uma função
#           existente no dicionario de funções recebidas do exterior.
# O resultado dessa função irá ser retornada para a variável (a), criada em runTime (exec('a = self.' + opt + str(vars)))
# O retorno feito será o dessa variável local (a) (return locals()['a'])

    def __getattr__(self, opt):
        global newFuncs
        return newFuncs[opt]

# Input: asyncore.dispatcher; Servermanager(para que seja possivel aceder às funções do servidor aquando a resposta do cliente)
# Contexto: Aqui é feita gestão do Json recebido do cliente e o posterior envio da resposta

class EchoHandler(asyncore.dispatcher, ServerManager):
    def handle_read(self):
        self.notificationsList = ["notification", "update"]
        try:
            msg = self.recv(1024).decode()
            if msg:
                python_obj = json.loads(msg)
                if python_obj["method"] == "\help":
                    self.send(self.jsonMaker(self.giveWelcome(), python_obj["id"]).encode())
                elif python_obj["method"] == "\exit":
                    print("Client disconnected %s" % repr(self.addr))
                    self.close()
                else:
                    if python_obj["method"] in self.notificationsList:
                        print("notification received")
                    else:
                        print("Message received from %s" % repr(self.addr))
                        print(python_obj)
                        result = self.funcoes(python_obj["method"], self.parametersExtract(python_obj))
                        if type(result) == tuple:
                            result = result[0]
                        print("Sending json message: ", self.jsonMaker(result, python_obj["id"]))
                        self.send(self.jsonMaker(result, python_obj["id"]).encode())
        except:
            pass
            # import traceback
            # traceback.print_exc()
            print("Something went wrong\nA team of highly trained monkeys has been dispatched")

# Output: Lista de funções existentes no servidor em conjunto com as registadas na declaração do mesmo
# Contexto: A lista preparada e depois enviada ao cliente, tem o proposito de dar a conhecer quais as funções disponiveis no servidor

    def giveWelcome(self):
        try:
            global newFuncs
            print("Available functions : " + ', '.join(list(newFuncs.keys()) + insideFuncs))
            return list(newFuncs.keys()) + insideFuncs
        except:
            pass
            #import traceback
            #traceback.print_exc()

# Input: asyncore.dispatcher
# Contexto: Inicialização do servidor

class Server(asyncore.dispatcher):

    # Input: endereço do servidor, porta do servidor

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print('Server up and running on %s:%s' % (host, port))

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('New client connect from %s' % repr(addr))
            handler = EchoHandler(sock)
