import socket

def client_main(server_ip, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")

        buffer=""
        while True:
            data = s.recv(1024)
            if not data:
                break
            buffer += data.decode()

            # 处理所有完整的消息
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                if message=="Game Over":
                    print("Game Over")
                    return
                process_message(s, message)
        
def receive_messages(sock, message_received_event):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data or data.lower() == 'quit':
                break
            print(f"Received from server: {data}")
            message_received_event.set()  # Signal that a message has been received
        except Exception as e:
            print(f"Error receiving data: {e}")
            break



def process_message(sock, message):
    if message.startswith("Broadcast: "):
        print(message[len("Broadcast: "):])
    elif message.startswith("Info: "):
        print(message[len("Info: "):])
    elif message.startswith("Input: "):
        user_input = input(message[len("Input: "):])
        sock.sendall(user_input.encode() + b'\n')  # 发送回应给服务器
    else:
        print(message)


# 使用示例
client_main('127.0.0.1', 65432)
