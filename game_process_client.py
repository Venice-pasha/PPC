import socket
import time

def client_main(server_ip, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port)) # Establish connection with server
        print(f"Connected to server at {server_ip}:{server_port}")

        buffer=""
        while True:
            data = s.recv(1024)
            if not data:
                break
            buffer += data.decode()

            # Process complete messages separated by newline
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                if message.startswith("Broadcast: Game over"):
                    print("Game Over")
                    time.sleep(2)
                    return
                else:
                    process_message(s, message)

def process_message(sock, message):
    if message.startswith("Input: "):
        user_input = input(message[len("Input: "):])
        sock.sendall(user_input.encode() + b'\n')  
        # if input, Send response back to server
    else:
        print(message)
        # or just print it

client_main('127.0.0.1', 65432)
