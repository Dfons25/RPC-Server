import socket
import json
import os

# Inicialização do cliente

# Classe responsável gestão do cliente:
#     Pedido ao servidor das funções disponíveis (self.serverFunctions = self.outHandler("welcome"))

class Client():

# Input: endereço do servidor, porta do cliente, opção se a shell está ou não activa
# Contexto: É criado o ciclo sobre o qual o cliente irá executar até haver um /exit ou /exitShell por parte do utilizador

    def __init__(self, host, port, shell):
        try:
            self.id = 0
            self.notificationsList = ["notification", "\exit", "\exitShell", "update"]
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))

            print("Connected to server")
            self.serverFunctions = self.outHandler("welcome")
            print("Available server functions: " + ', '.join(self.serverFunctions))
            print("Available client functions: " + ', '.join(self.notificationsList))
            if shell:
                connected = True
                while connected:
                    msg = input("> ")
                    if msg == "\exit":
                        self.exit()
                        os._exit(0)
                        break
                    if msg == "\exitShell":
                        print("Exit from the shell successful - Running scripts after start of client")
                        break
                    if msg == "\help":
                        self.help();
                    else:
                        try:
                            msg = self.insertSelf(msg, self.serverFunctions + self.notificationsList)
                            exec (msg)
                        except:
                            #import traceback
                            #traceback.print_exc()
                            print("Function not avaliable. Use \help to check the options")
                            pass
        except:
            #import traceback
            #traceback.print_exc()
            print("Problem connecting to server")

# Input: Função invocada não encontrada
# Output: Resultado retornado pelo servidor
# Contexto: Caso a função não seja encontrada, a mesma será redirecionada para aqui
#           Caso o nome da função faça parte da lista de nomes recebidos pelo servidor ou da lista de notificações
#           é devolvido uma função (wrapper) que irá entregar ao outHandler o nome da função que deu a excepção (tem acesso ao nome, pois está dentro da origem)
#           em conjunto com as variaveis a serem utilizadas nessa mesma função

    def __getattr__(self, attr):
        try:
            if attr in self.serverFunctions or attr in self.notificationsList:
                def wrapper(*arg):
                    return self.outHandler(attr, *arg)
                return wrapper
        except:
            print("Something went wrong, check your connection to the server")
            os._exit(0)
            pass

# Input: Input introduzido na shell pelo utilizador
# Output: Input do utilizador devidamente formatado
# Contexto: Estando dentro de uma classe, todas as funções tem de ser invocadas com o formato self.nomeDaFunção
#           É percorrida a lista de funções existentes e feito um replace para acrescentar "self." à declaração do utilizador

    def insertSelf(self, text, list):
        for i in list:
            text = text.replace(i, "self." + i)
        return text

# Input: Opção correspondente à função a ser utilizada; Variaveis a serem utilizadas como argumentos na função
# Output: Caso a função não faça parte da lista de notificações, retorna o resultado do envio de dados ao servidor

    def outHandler(self, opt, *arg):
        try:
            self.client_socket.sendall(self.jsonMaker(opt, *arg).encode())
            if not opt in self.notificationsList:
                return self.jsonDemaker(self.client_socket.recv(1024).decode())
        except:
            #import traceback
            #traceback.print_exc()
            pass
        return "none"

# Input: Opção correspondente à função a ser utilizada; Variaveis a serem utilizadas como argumentos na função
# Output: Mensagem formata em Json a ser enviada ao utilizador

    def jsonMaker(self, opt, *arg):
        final = {"jsonrpc": "2.0"}
        if opt in self.notificationsList:
            final.update({"method": opt, "params": arg})
        else:
            self.id = self.id + 1
            final.update({"id": self.id , "method": opt, "params": arg})
        return json.dumps(final)

# Input: Mensagem em Json proveniente do servidor
# Output: Valores existentes no parametro "result"

    def jsonDemaker(self, message):
        python_obj = json.loads(message)
        return python_obj["result"]

# Contexto: Possibilidade de chamar o menu de ajuda quando a classe é instânciada no exterior

    def help(self):
        self.serverFunctions = self.outHandler("\help")
        print("Available server functions: " + ', '.join(self.serverFunctions))
        print("Available client functions: " + ', '.join(self.notificationsList))

# Contexto: Possibilidade de sair quando a classe é instânciada no exterior

    def exit(self):
        self.outHandler("\exit")
        print("Exit from the server successful")
        self.client_socket.close()

