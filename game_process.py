import threading
import queue
import random
import structure as s 
import socket
import copy
import multiprocessing
import time

class Game:
    def __init__(self, number_of_players):
        manager=multiprocessing.Manager()
        self.number_of_players = number_of_players
        self.deck = self.create_deck()
        self.players_hands = manager.list([None] * number_of_players)
        self.lock = multiprocessing.Lock()
        self.information_tokens= multiprocessing.Value('i', number_of_players+3)
        self.fuse_tokens = multiprocessing.Value('i', 3)
        self.victory_pool = manager.dict(self.create_victory_pool())
        self.init_barrier = multiprocessing.Barrier(number_of_players + 1)
        self.to_main_queue = multiprocessing.Queue()  # 子线程向主线程发送消息的队列
        self.to_child_queues = [multiprocessing.Queue() for _ in range(number_of_players)]  # 主线程向子线程发送消息的队列
        self.turn_condition = multiprocessing.Condition(self.lock)
        self.game_over = multiprocessing.Event()
        self.current_turn = multiprocessing.Value('i',0)
        self.played_cards=manager.list()
        listen_process=threading.Thread(target=self.listen_to_son, args=())
        listen_process.start()
        self.turn_start = [multiprocessing.Event() for _ in range(number_of_players)]
        self.turn_end = [multiprocessing.Event() for _ in range(number_of_players)]
        self.server_main('127.0.0.1', 65432)



    def server_main(self,server_ip, server_port):
    # 存储客户端连接
        client_connections = []

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((server_ip, server_port))
            s.listen()

            print(f"Server listening on {server_ip}:{server_port}. Waiting for {self.number_of_players} players to connect.")

            # 等待直到所有玩家连接
            while len(client_connections) < self.number_of_players:
                conn, addr = s.accept()
                print(f"Player connected from {addr}")
                client_connections.append(conn)
            self.client_connections=client_connections
            # 所有玩家都已连接，开始主游戏逻辑
            print("All players connected. Starting game.")
                    # 创建和启动玩家线程
            self.player_processes = []
            for i in range(self.number_of_players):
                process = multiprocessing.Process(target=self.player_action, args=(i,))
                self.player_processes.append(process)
                process.start()
            self.init_barrier.wait()
            time.sleep(3)
            #index=0事件开始
            while not self.game_over.is_set():
                with self.lock:
                    current_player = self.current_turn.value
                self.turn_start[current_player].set()  # 通知当前玩家开始回合
                self.turn_end[current_player].wait()
                self.turn_end[current_player].clear()
                with self.lock:
                    self.current_turn.value = (self.current_turn.value + 1) % self.number_of_players
            # self.game_barrier.wait()
            # 等待所有线程完成
            for process in self.player_processes:
                process.join()


    def broadcast(self, message):
        encoded_message = f"Broadcast: {message}".encode()
        for conn in self.client_connections:
            try:
                conn.sendall(encoded_message)
            except socket.error as e:
                print(f"Error sending message to client: {e}")
    
    def unicast_info(self,message,index):
        if index < len(self.client_connections):
            encoded_message = f"Info: {message}".encode()
            try:
                self.client_connections[index].sendall(encoded_message)
            except socket.error as e:
                print(f"Error sending info to client {index}: {e}")
        else:
            print(f"Invalid client index: {index}")


    def unicast_input(self,message,index):
        if index < len(self.client_connections):
            encoded_message = f"Input: {message}".encode()
            response_received=False
            try:
                conn = self.client_connections[index]
                conn.sendall(encoded_message)
                while not response_received:
                    try:
                        conn.settimeout(0.1)
                        response = conn.recv(1024).decode().strip()
                        if response:
                            response_received = True
                            return response
                    except socket.timeout:
                        pass
            except socket.error as e:
                print(f"Error sending input request to client {index}: {e}")
        else:
            print(f"Invalid client index: {index}")


    def close_all_connections(self):
        """关闭所有客户端连接"""
        for conn in self.client_connections:
            conn.close()
        self.client_connections = []

    def listen_to_son(self):
        while not self.game_over.is_set():
            while not self.to_main_queue.empty():
                message = self.to_main_queue.get()
                print("Main thread received:", message)
                if message.startswith("Information"):
                    parts = message.split(":")
                    player_dest = int(parts[1].split()[1])  # 假设消息格式正确

                    # 修改消息格式并发送给相应的玩家
                    new_message = f"to player {player_dest}: {message}"
                    self.to_child_queues[player_dest].put(new_message)
                elif message.startswith("Play"):
                    for i in range(self.number_of_players):
                        self.to_child_queues[i].put(message)
                elif message.startswith("Discard"):
                    for i in range(self.number_of_players):
                        self.to_child_queues[i].put(message)
                elif message.startwith("choose action:"):
                    pass
                else:
                    # 处理其他类型的消息
                    pass

    def create_deck(self):
        if self.number_of_players == 2:
            self.colors = ['Red', 'Bleu'] 
        if self.number_of_players == 3:
            self.colors = ['Red', 'Bleu', 'Green']
        numbers = [1]*3 + [2]*2 + [3]*2 + [4]*2 + [5]
        deck = s.Deck(self.colors, numbers) 
        return deck
    
    def create_victory_pool(self):
        return {color: 0 for color in self.colors}
    
    def show_sight(self,player_index):
        with self.lock:
            message=(f"show {player_index}'s sight\n")
            self.unicast_info(message,player_index)
            for index, player_hand in enumerate(self.players_hands):
                if index != player_index:
                    message=(f"Player {index}'s cards: {player_hand}\n")
                    self.unicast_info(message,player_index)
                else:
                    message=(f"You are {index} you cannot see your card\n")
                    self.unicast_info(message,player_index)

    def print_vpool(self,player_index):
        with self.lock:
            message=("Victory Pool:")
            self.unicast_info(message,player_index)
            for color, highest_number in self.victory_pool.items():
                message=(f"  Color {color}: highest card number {highest_number}\n")
                self.unicast_info(message,player_index)
            total_cards = sum(self.victory_pool.values())
            total_score = total_cards
            message=(f"Total score: {total_score}\n")
            self.unicast_info(message,player_index)

    def is_game_over(self):
        # case1: victory
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            message=("Victory! All fireworks are completed.\n")
            self.broadcast(message)
            self.game_over=True
        # case2: fuse token all used
        if self.fuse_tokens.value == 0:
            message=("Game over! All fuse tokens are used.\n")
            self.broadcast(message)
            self.game_over=True
        # case3: deck all used
        if not self.deck:
            message=("Game over! No more cards in the deck.\n")
            self.broadcast(message)
            self.game_over=True
        message=("Game continues.\n")
        self.broadcast(message)

    def card_action(self, player_index,player_hand):
        action=self.input_action(player_index)
        action_success=False
        while not action_success:
            if action == 'inform':
                action_success=self.inform(player_index)
            elif action == 'play':
                action_success=self.play_card(player_index,player_hand)
            elif action == 'discard':
                action_success=self.discard_card(player_index,player_hand)

    def input_action(self,player_index):
        input_sucess=False
        while not input_sucess:
            message=(f"input action of {player_index}:type your action index,1 for inform, 2 for play card,3 for discard\n")
            action_index=self.unicast_input(message,player_index)
            if action_index=='1':
                if self.information_tokens.value <= 0:
                    message=("No information tokens left. Cannot give information.\n")
                    self.unicast_info(message,player_index)
                else:
                    input_sucess=True
                    action='inform'
            elif action_index=='2':
                input_sucess=True
                action='play'
            elif action_index=='3':
                input_sucess=True
                action='discard'
            else:
               message=("wrong index!Try again.\n")
               self.unicast_info(message,player_index)
        return action

    def inform(self,player_index):
        # input and verify the info dest
        input_sucess=False
        while not input_sucess:
            message=(f"input action of {player_index}:type player dest\n")
            player_dest=self.unicast_input(message,player_index)
            if player_dest.isdigit():
                player_dest=int(player_dest)
                if player_index==player_dest:
                    message=("Can not use info token to yourself!\n")
                    self.unicast_info(message,player_index)
                elif player_dest>=self.number_of_players or player_dest<0:
                    message=("illegal index! The number you type must be limited into the number of player!\n")
                    self.unicast_info(message,player_index)
                else:
                    input_sucess=True
            else:
                print("type an int!\n")
        # input and verify the action info
        input_sucess=False
        while not input_sucess:
            message=("action of inform, type a color or a number of card\n")
            action_info=self.unicast_input(message,player_index)
            if action_info.isdigit() and int(action_info) in [1, 2, 3, 4, 5]:
                action_info = int(action_info)
                input_sucess = True
                input_type = 'number'
            elif action_info in self.colors:
                input_sucess = True
                input_type = 'color'
            else:
                message=("illegal info!\n")
                self.unicast_info(message,player_index)
                time.sleep(0.5)
        # Execution
        with self.lock:
            self.information_tokens.value -= 1
        player_hand=self.players_hands[player_dest]
        if (input_type == 'color'):
            qty,place=self.info_cardcolor(player_hand,action_info)
            message=(f"#Information from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        elif (input_type == 'number'):
            qty,place=self.info_cardnumber(player_hand,action_info)
            message=(f"Information from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        self.to_main_queue.put(message)
            #把这条信息发送信息给主程序
        return True
            
    #level 4 programme, subject of inform
    def info_cardnumber(self,player_hand,n):
        count = 0
        positions = []
        for index, card in enumerate(player_hand):
            number=int(card.number)
            n=int(n)
            if number == n:
                count += 1
                positions.append(index)
        return count, positions

    #level 4 programme, subject of inform
    def info_cardcolor(self,player_hand,c):
        count = 0
        positions = []
        for index, card in enumerate(player_hand):
            if card.color == c:
                count += 1
                positions.append(index)
        return count, positions

    def play_card(self, player_index, player_hand):
        input_success=False
        while not input_success:
            message="which card do you want to play, choose from 0 to 4:"
            card_index=self.unicast_input(message,player_index)
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                message=("illegal info!\n")
                self.unicast_info(message,player_index)
        card_played=copy.deepcopy(player_hand[card_index])
        color=card_played.color
        number=card_played.number
        '''with self.lock:
            if self.victory_pool[color] == number-1:
                self.victory_pool[color] = number
                message=(f"Play:you added sucessfully{card_index} with {color} and {number} to victory pool!\n")
            else:
                self.fuse_tokens.count -=1
                self.played_cards.append(card_played)
                message=(f"Play:you droped your {card_index} with {color} and {number} and lose a fuse_token!\n")'''
        if self.victory_pool[color] == number-1:
            self.victory_pool[color] = number
            message=(f"Play:Player{player_index} added sucessfully card{card_index} with {color} and {number} to victory pool!\n")
        else:
            with self.lock:
                self.fuse_tokens.value -=1
            self.played_cards.append(card_played)
            message=(f"Play:Player{player_index} droped card{card_index} with {color} and {number} and lose a fuse_token!\n")
        
        self.to_main_queue.put(message)
        '''with self.lock:
            player_hand[player_index]=self.deck.draw_card()
            self.players_hands[player_index]=player_hand'''
        player_hand[player_index]=self.deck.draw_card()
        with self.lock:
            self.players_hands[player_index]=player_hand
        print("a new card is in your hand, replace the card you've used.\n ")
        return True
    
    #level 3 programme, 3rd kind
    def discard_card(self, player_index):
        input_success=False
        while not input_success:
            card_index=input("which card do you want to throw away, choose from 0 to 4:")
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                print("illegal info!")
        player_hand=self.players_hands[player_index]
        discard=copy.deepcopy(player_hand.cards[card_index])
        self.played_cards.append(discard)
        (self.players_hands[player_index].cards)[card_index]=self.deck.draw_card()
        print("a new card is in your hand, replace the card you've used.\n ")
        '''with self.lock:
            self.information_tokens += 1'''
        self.information_tokens += 1
        message=("Discard:We've got a new info token. Vivez la nouvelle regle!")
        self.to_main_queue.put(message)
        return True

    def player_action(self, player_index):
        listen_thread = threading.Thread(target=self.listen_to_main, args=(player_index,))
        listen_thread.start()
        player_hand=[]
        for _ in range(5): 
            '''with self.lock:'''
            card = self.deck.draw_card()
            if card:
                player_hand.append(card)
        with self.lock:
            self.players_hands[player_index]=player_hand
        self.players_hands[player_index]=player_hand
        self.init_barrier.wait()

        while not self.game_over.is_set(): 
            self.turn_start[player_index].wait()
            self.turn_start[player_index].clear()
            if self.game_over.is_set():
                break
            message=(f"{player_index}'s turn!\n")
            self.broadcast(message)
            self.show_sight(player_index)
            self.print_vpool(player_index)
            self.card_action(player_index,player_hand)
            self.is_game_over()
            message=(f"player {player_index} finished")
            self.broadcast(message)
            self.turn_end[player_index].set()
        #self.game_barrier.wait()
        listen_thread.join()

    def listen_to_main(self, player_index):
        while not self.game_over.is_set():
            if not self.to_child_queues[player_index].empty():
                message = self.to_child_queues[player_index].get()
                try:
                    self.unicast_info(message,player_index)
                except socket.error as e:
                    print(f"Error sending message to player {player_index}: {e}")


            

# 运行游戏
game = Game(number_of_players=2)
