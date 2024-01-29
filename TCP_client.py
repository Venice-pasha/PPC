import socket
import threading

import socket
import threading

class GameClient:
    def __init__(self, host, port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.game_started = threading.Event()

    def listen_for_server_messages(self):
        while not self.game_started.is_set():
            message = self.client_socket.recv(1024).decode()
            print(message)
            if "Starting the game!" in message:
                self.game_started.set()

    def send_messages_to_server(self):
        while not self.game_started.is_set():
            message = input("print start to start the game, or wait other player to do this: ")
            self.client_socket.sendall(message.encode())
            if message.lower() == "start":
                break  # 可选：发送 'start' 后退出发送循环

    def receive_message(self,client_socket):
        message = client_socket.recv(1024).decode()
        if message.startswith("game_info:"):
            self.handle_game_info(message[len("game_info:"):])
        elif message.startswith("input_ask:"):
            return self.handle_input_ask(client_socket, message[len("input_ask:"):])

    def handle_game_info(self,info):
        print("Game Info:", info)

    def handle_input_ask(self,client_socket, prompt):
        print(prompt)
        response = input()
        client_socket.sendall(response.encode())
        return response

    def start(self):
        threading.Thread(target=self.listen_for_server_messages).start()
        threading.Thread(target=self.send_messages_to_server).start()
        self.game_started.wait()
        print("Game has started. ")

# 使用示例
client = GameClient('127.0.0.1', 60000)
client.start()
while True:
    client.receive_message(client.client_socket)