import socket
import threading
import json

HOST = ""
PORT = 12345

class Server:

    def __init__(self, host = "", port = 12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(2)
        print("Searching for players...")

        self.connections = []
        self.clients = {}

    def add_client(self, c, name):
        self.connections.append(c)
        self.clients[c] = name
        if len(self.connections) == 2:
            for i in range(len(self.connections)):
                self.connections[i].send(json.dumps({"action" : "game", "id" : i}).encode("utf-8"))
        else:
            for c in self.connections:
                c.send(json.dumps({"action" : "wait"}).encode("utf-8"))


    def recv(self, c):
         while True:
            
            raw_data = c.recv(1024).decode("utf-8")

            if not raw_data:
                print(self.clients[c], "has logged out")
                del self.clients[c]
                self.connections.remove(c)
                break

            i = 0
            while i < len(raw_data):
                j = raw_data.find('}', i)
                data = json.loads(raw_data[i:j + 1])
                i = j + 1   

                if data["action"] == "play":
                    for conn in self.connections:
                        if conn != c:
                            conn.send(json.dumps({"action" : "play", "ij" : data["ij"], "color" : data["color"]}).encode("utf-8"))

                if data["action"] == "end_game":
                    for conn in self.connections:
                        if conn != c:
                            conn.send(json.dumps({"action" : "end_game"}).encode("utf-8"))
                    print(self.clients[c], "has logged out")
                    del self.clients[c]
                    self.connections.remove(c)
                    return

                if data["action"] == "quit":
                    for conn in self.connections: 
                        if conn != c:
                            conn.send(json.dumps({"action" : "quit"}).encode("utf-8"))
                    print(self.clients[c], "has logged out")
                    del self.clients[c]
                    self.connections.remove(c)
                    return

    def run(self):

        while True:
            c, addr = self.socket.accept()

            data = c.recv(1024).decode("utf-8")
            data = json.loads(data)
    
            print(data["name"] + " has logged in")
            c.send(json.dumps({"action" : "welcome"}).encode("utf-8"))
            self.add_client(c, data["name"])
            
            threading.Thread(target = self.recv, args = (c,)).start()

if __name__ == "__main__":

    server = Server(HOST, PORT)
    server.run()





