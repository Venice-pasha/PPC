import socket
import threading
import structure as s
import random
import time
import copy

class GameServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.game_started = threading.Event()  # 用于控制游戏开始的标志

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")
        self.start_game=threading.Event()
        while not self.start_game.is_set():
            client_socket, addr = self.server_socket.accept()
            print(f"Connected by {addr}")
            self.clients.append(client_socket)

            # 为每个连接的客户端启动一个线程
            threading.Thread(target=self.listen_for_start_command, args=(client_socket,)).start()
            if len(self.clients)==2:
                time.sleep(10)
            elif len(self.clients)==3:
                break

    def listen_for_start_command(self, client_socket):
        while not self.start_game.is_set():
            start_command = client_socket.recv(1024).decode()
            if start_command.lower() == "start":
                self.start_game.set()  # 设置标志以开始游戏
                message = "Starting the game!\n"
                print(message)
                self.send_all(message)
                return  # 退出线程

    # 3 kinds of message of server
    def send_game_info(self,player_index, info):
        client_socket= self.clients[player_index]
        message = f"game_info:{info}"
        client_socket.sendall(message.encode())
    def ask_input(self,player_index, prompt):
        client_socket= self.clients[player_index]
        message = f"input_ask:{prompt}"
        client_socket.sendall(message.encode())
        response = client_socket.recv(1024).decode()
        return response
    def send_all(self,message):
        for client in self.clients:
            client.sendall(message.encode())
        
    def init_game(self):
        number_of_players=len(self.clients)
        self.number_of_players = number_of_players
        self.players_hands = [s.PlayerHand() for _ in range(number_of_players)]
        self.played_cards = []
        self.deck = self.create_deck()
        self.information_tokens, self.fuse_tokens = self.create_tokens()
        self.deal_cards()
        self.victory_pool = self.create_victory_pool()

    # init_game/programme
    def create_deck(self):
        if self.number_of_players == 2:
            self.colors = ['Red', 'Bleu'] 
        if self.number_of_players == 3:
            self.colors = ['Red', 'Bleu', 'Green']
        numbers = [1]*3 + [2]*2 + [3]*2 + [4]*2 + [5]
        deck = [s.Card(color, number) for color in self.colors for number in numbers]
        random.shuffle(deck)
        return deck
    def create_tokens(self):
        information_tokens = s.Token('information', self.number_of_players + 3)
        fuse_tokens = s.Token('fuse', 3)
        return information_tokens, fuse_tokens
    def deal_cards(self):
        for player_hand in self.players_hands:
            for _ in range(5):
                player_hand.add_card(self.deck.pop())
    def create_victory_pool(self):
        return {color: 0 for color in self.colors}
    

    def play_game(self):
        while True:
            for player_index in range(self.number_of_players):
                self.show_sight(player_index)
                self.show_vpool(player_index)
                self.player_action(player_index)
                stop=self.is_game_over()
                if stop:
                    self.print_vpool()
                    break


    # play_game/programme
    def show_sight(self,player_index):
        for index, player_hand in enumerate(self.players_hands):
            if index != player_index:
                message=(f"Player {index}'s cards: {player_hand}\n")
                self.send_game_info(player_index,message)
            else:
                message=(f"You are {index} you cannot see your card\n")
                self.send_game_info(player_index,message)
    def is_game_over(self):
        # case1: victory
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            message="Victory! All fireworks are completed.\n"
            self.sendall(message)
            return True
        # case2: fuse token all used
        if self.fuse_tokens.count == 0:
            message="Game over! All fuse tokens are used.\n"
            self.sendall(message)
            return True
        # case3: deck all used
        if not self.deck:
            message="Game over! No more cards in the deck.\n"
            self.sendall(message)
            return True
        message="Game continues.\n"
        self.send_all(message)
        return False
    def show_vpool(self,player_index):
        message=("Victory Pool:\n")
        self.send_game_info(player_index,message)
        for color, highest_number in self.victory_pool.items():
            message=(f"  Color {color}: highest card number {highest_number}")
            self.send_game_info(player_index,message)
        total_cards = sum(self.victory_pool.values())
        total_score = total_cards
        message=(f"Total score: {total_score}")
        self.send_game_info(player_index,message)
################

    #level 2 programme, action of one player
    def player_action(self, player_index):
        self.input_action(player_index)
        action_success=False
        while not action_success:
            if self.action == 'inform':
                action_success=self.inform(player_index)
            elif self.action == 'play':
                action_success=self.play_card(player_index)
            elif self.action == 'discard':
                action_success=self.discard_card(player_index)

    #level 3 programme, subject of player action, check input of player
    def input_action(self,player_index):
        input_sucess=False
        while not input_sucess:
            message=("type your action index,1 for inform, 2 for play card,3 for discard\n")
            action_index=self.ask_input(player_index,message)
            if action_index=='1':
                if self.information_tokens.count <= 0:
                    message=("No information tokens left. Cannot give information.\n")
                    self.send_game_info(player_index,message)
                else:
                    input_sucess=True
                    self.action='inform'
            elif action_index=='2':
                input_sucess=True
                self.action='play'
            elif action_index=='3':
                input_sucess=True
                self.action='discard'
            else:
                message=("wrong index!Try again.\n")
                self.send_game_info(player_index,message)
    
    #level 3 programme, 1st kind of action
    def inform(self,player_index):
        # input and verify the info dest
        input_sucess=False
        while not input_sucess:
            message=("type player dest")
            player_dest=self.ask_input(player_index,message)
            if player_dest.isdigit():
                player_dest=int(player_dest)
                if player_index==player_dest:
                    message=("Can not use info token to yourself!\n")
                    self.send_game_info(player_index,message)
                elif player_dest>=self.number_of_players or player_dest<0:
                    message=("illegal index! The number you type must be limited into the number of player!\n")
                    self.send_game_info(player_index,message)
                else:
                    input_sucess=True
            else:
                message=("type an int!\n")
                self.send_game_info(player_index,message)
        # input and verify the action info
        input_sucess=False
        while not input_sucess:
            message=("action of inform, type a color or a number of card\n")
            action_info=self.ask_input(player_index,message)
            if action_info.isdigit() and int(action_info) in [1, 2, 3, 4, 5]:
                action_info = int(action_info)
                input_sucess = True
                input_type = 'number'
            elif action_info in self.colors:
                input_sucess = True
                input_type = 'color'
            else:
                message=("illegal info!\n")
                self.send_game_info(player_index,message)
        # Execution
        self.information_tokens.count -= 1
        player_hand=self.players_hands[player_dest]
        if (input_type == 'color'):
            qty,place=self.info_cardcolor(player_hand,action_info)
            message=(f"from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        elif (input_type == 'number'):
            qty,place=self.info_cardnumber(player_hand,action_info)
            message=(f"from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        self.send_all(message)
        return True
            
    #level 4 programme, subject of inform
    def info_cardnumber(self,player_hand,n):
        count = 0
        positions = []
        for index, card in enumerate(player_hand.cards):
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
        for index, card in enumerate(player_hand.cards):
            if card.color == c:
                count += 1
                positions.append(index)
        return count, positions

    #level 3 programme, 2nd kind
    def play_card(self, player_index):
        input_success=False
        while not input_success:
            message=input("which card do you want to play, choose from 0 to 4:")
            card_index=self.ask_input(player_index,message)
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                message=("illegal info!\n")
                self.send_game_info(player_index,message)
        player_hand=self.players_hands[player_index]
        card_played=copy.deepcopy(player_hand.cards[card_index])
        color=card_played.color
        number=card_played.number
        if self.victory_pool[color] == number-1:
            self.victory_pool[color] = number
            message=(f"you added sucessfully{card_index} with {color} and {number} to victory pool!\n")
        else:
            self.fuse_tokens.count -=1
            self.played_cards.append(card_played)
            message=(f"you droped your {card_index} with {color} and {number} and lose a fuse_token!\n")
        self.send_game_info(player_index,message)
        (self.players_hands[player_index].cards)[card_index]=self.deck.pop()
        message=("a new card is in your hand, replace the card you've used.\n ")
        self.send_game_info(player_index,message)
        return True
    
    #level 3 programme, 3rd kind
    def discard_card(self, player_index):
        input_success=False
        while not input_success:
            message=input("which card do you want to throw away, choose from 0 to 4:")
            card_index=self.ask_input(player_index,message)
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                message=("illegal info!")
                self.send_game_info(player_index,message)
        player_hand=self.players_hands[player_index]
        discard=copy.deepcopy(player_hand.cards[card_index])
        self.played_cards.append(discard)
        (self.players_hands[player_index].cards)[card_index]=self.deck.pop()
        message=("a new card is in your hand, replace the card you've used.\n ")
        self.send_game_info(player_index,message)
        self.information_tokens += 1
        message=("you've got a new info token.")
        self.send_all(message)
        return True
###################dev
    
# run code
server = GameServer('127.0.0.1', 60000)
server.start_server()
server.init_game()
server.play_game()
