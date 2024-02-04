import threading
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
        self.players_hands = manager.list()
        for _ in range(number_of_players):
            player_hand = [self.deck.draw_card() for _ in range(5)]
            self.players_hands.append(player_hand)
        self.lock = multiprocessing.Lock()
        self.information_tokens= multiprocessing.Value('i', number_of_players+3)
        self.fuse_tokens = multiprocessing.Value('i', 3)
        self.victory_pool = manager.dict(self.create_victory_pool())
        self.init_barrier = multiprocessing.Barrier(number_of_players + 1)
        self.to_main_queue = multiprocessing.Queue()
        self.to_child_queues = [multiprocessing.Queue() for _ in range(number_of_players)] 
        self.turn_condition = multiprocessing.Condition(self.lock)
        self.game_over = multiprocessing.Event()
        self.current_turn = multiprocessing.Value('i',0)
        self.played_cards=manager.list()
        listen_process=threading.Thread(target=self.listen_to_son, args=())
        listen_process.start()
        self.turn_start = [multiprocessing.Event() for _ in range(number_of_players)]
        self.turn_end = [multiprocessing.Event() for _ in range(number_of_players)]
        self.server_main('127.0.0.1', 65432)
        print(self.victory_pool)
        total_cards = sum(self.victory_pool.values())
        total_score = total_cards
        print(f"Total score: {total_score}\n")
        print("end game!")


    '''
    manager: Used to create shared variables that are safe in a multiprocessing context.
    number_of_players: The number of players in the game.
    deck: A pile of cards containing all the cards needed for the game.
    players_hands: A shared list storing the hand of cards for each player.
    lock: A multiprocessing lock used for synchronizing access to shared resources.
    information_tokens: Stores the number of information tokens in the game.
    fuse_tokens: Stores the number of fuse tokens in the game.
    victory_pool: Records the highest number for each color of card.
    init_barrier: A barrier to ensure all processes are ready before starting the game.
    to_main_queue: A queue for child processes to send messages to the main process.
    to_child_queues: An array of queues for each player, used for the main process to send messages to child processes.
    game_over: An event flag to indicate whether the game has ended.
    current_turn: The number of the player whose turn it currently is.
    played_cards: Stores cards that have been played or discarded.
    listen_process: A listening thread for handling messages sent from child processes to the main process.
    turn_start and turn_end: Arrays of event flags to control the start and end of each player's turn.
    '''

    #Sets up the server, waits for players to connect, and initiates game logic.
    def server_main(self,server_ip, server_port):
        client_connections = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((server_ip, server_port))
            s.listen()
            print(f"Server listening on {server_ip}:{server_port}. Waiting for {self.number_of_players} players to connect.")
            while len(client_connections) < self.number_of_players:
                conn, addr = s.accept()
                print(f"Player connected from {addr}")
                client_connections.append(conn)
            self.client_connections=client_connections
            print("All players connected. Starting game.")
            self.player_processes = []
            for i in range(self.number_of_players):
                process = multiprocessing.Process(target=self.player_action, args=(i,))
                self.player_processes.append(process)
                process.start()
            self.init_barrier.wait()
            time.sleep(3)
            while not self.game_over.is_set():
                with self.lock:
                    current_player = self.current_turn.value
                self.turn_start[current_player].set()  
                self.turn_end[current_player].wait()
                if self.game_over.is_set():
                    break
                self.turn_end[current_player].clear()
                with self.lock:
                    self.current_turn.value = (self.current_turn.value + 1) % self.number_of_players
            for process in self.player_processes:
                process.join()

    # Broadcasts a message to all clients.
    def broadcast(self, message):
        encoded_message = f"Broadcast: {message}".encode()
        for conn in self.client_connections:
            try:
                conn.sendall(encoded_message)
            except socket.error as e:
                print(f"Error sending message to client: {e}")
    
    # Sends information to a specified client.
    def unicast_info(self,message,index):
        if index < len(self.client_connections):
            encoded_message = f"Info: {message}".encode()
            try:
                self.client_connections[index].sendall(encoded_message)
            except socket.error as e:
                print(f"Error sending info to client {index}: {e}")
        else:
            print(f"Invalid client index: {index}")

    # Requests and retrieves input from a specified client.
    def unicast_input(self,message,index):
        if index < len(self.client_connections):
            encoded_message = (f"Input: {message}").encode()
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

    # Closes all client connections.
    def close_all_connections(self):
        for conn in self.client_connections:
            conn.close()
        self.client_connections = []

    #  Listens for messages sent from child processes to the main process.
    def listen_to_son(self):
        while not self.game_over.is_set():
            while not self.to_main_queue.empty():
                message = self.to_main_queue.get()
                print("Main thread received:", message)
                if message.startswith("Information"):
                    parts = message.split(":")
                    player_dest = int(parts[1].split()[1]) 
                    new_message = f"to player {player_dest}: {message}"
                    self.to_child_queues[player_dest].put(new_message)
                elif message.startswith("Play"):
                    for i in range(self.number_of_players):
                        self.to_child_queues[i].put(message)
                elif message.startswith("Discard"):
                    for i in range(self.number_of_players):
                        self.to_child_queues[i].put(message)
                else:
                    pass

    # Creates and initializes the deck of cards.
    def create_deck(self):
        if self.number_of_players == 2:
            self.colors = ['Red', 'Bleu'] 
        if self.number_of_players == 3:
            self.colors = ['Red', 'Bleu', 'Green']
        numbers = [1]*3 + [2]*2 + [3]*2 + [4]*2 + [5]
        deck = s.Deck(self.colors, numbers) 
        return deck
    
    # Initializes the victory pool.
    def create_victory_pool(self):
        return {color: 0 for color in self.colors}
    
    # Shows other players' hands to a specified player.
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

    # Prints the state of the victory pool to a specified player.
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

    # Checks if the game is over and processes accordingly.
    def is_game_over(self):
        # case1: victory
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            message = "Game over: Victory! All fireworks are completed.\n"
        # case2: fuse token all used
        elif self.fuse_tokens.value == 0:
            message = "Game over: All fuse tokens are used.\n"
        # case3: deck all used
        elif not self.deck:
            message = "Game over: No more cards in the deck.\n"
        else:
            message = "Game continues.\n"

        # Broadcasting the message to all clients
        if "Game over" in message:
            for i in range(self.number_of_players):
                self.print_vpool(i)
                self.broadcast(message)
                self.game_over.set()  
                self.close_all_connections() 
                for event in self.turn_start:
                    event.set()

    # Handles the action chosen by the player (inform, play card, or discard).
    def card_action(self, player_index,player_hand):
        action=self.input_action(player_index)
        if action == 'inform':
            self.inform(player_index)
        elif action == 'play':
            self.play_card(player_index,player_hand)
        elif action == 'discard':
            self.discard_card(player_index)
        
    # Requests and gets the player's choice of action.
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
            time.sleep(0.5)
        return action

    # Processes the inform action.
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
        return True
            
    # Provide information about specific cards.
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
    def info_cardcolor(self,player_hand,c):
        count = 0
        positions = []
        for index, card in enumerate(player_hand):
            if card.color == c:
                count += 1
                positions.append(index)
        return count, positions

    # Processes the play card action.
    def play_card(self, player_index, player_hand):
        #ask for input
        input_success=False
        while not input_success:
            message="Input:which card do you want to play, choose from 0 to 4:\n:"
            card_index=self.unicast_input(message,player_index)
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                message=("illegal info!\n")
                self.unicast_info(message,player_index)
        #use card
        card_played=copy.deepcopy(player_hand[card_index])
        color=card_played.color
        number=card_played.number
        if self.victory_pool[color] == number-1:
            self.victory_pool[color] = number
            message=(f"Play:Player{player_index} added sucessfully card{card_index} with {color} and {number} to victory pool!\n")
        else:
            with self.lock:
                self.fuse_tokens.value -=1
            self.played_cards.append(card_played)
            message=(f"Play:Player{player_index} droped card{card_index} with {color} and {number} and lose a fuse_token!\n")
        self.to_main_queue.put(message)
        with self.lock:
            new_hand = list(self.players_hands[player_index])  
            new_hand[card_index] = self.deck.draw_card() 
            self.players_hands[player_index] = new_hand

        message=("a new card is in your hand, replace the card you've used.\n ")
        self.unicast_info(message,player_index)
        return True
    
    #Processes the discard card action.
    def discard_card(self, player_index):
        input_success=False
        while not input_success:
            message=("which card do you want to throw away, choose from 0 to 4:\n")
            card_index=self.unicast_input(message,player_index)
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                message="illegal info!\n"
                self.unicast_info(message,player_index)
        player_hand=self.players_hands[player_index]
        discard=copy.deepcopy(player_hand[card_index])
        self.played_cards.append(discard)
        with self.lock:
            (self.players_hands[player_index])[card_index]=self.deck.draw_card()
        message=("a new card is in your hand, replace the card you've used.\n ")
        self.unicast_info(message,player_index)
        with self.lock:
            self.information_tokens.value += 1
        message=("Discard:We've got a new info token. Vivez la nouvelle regle!\n")
        self.to_main_queue.put(message)
        return True

    # Controls the flow of a player's actions.
    def player_action(self, player_index):
        #initialisation
        listen_thread = threading.Thread(target=self.listen_to_main, args=(player_index,))
        listen_thread.start()
        self.init_barrier.wait()
        #loop to break game
        while not self.game_over.is_set(): 

            self.turn_start[player_index].wait()
            if self.game_over.is_set():
                listen_thread.join()
                break
            self.turn_start[player_index].clear()
            message=(f"{player_index}'s turn!\n")

            self.broadcast(message)
            player_hand=self.players_hands[player_index]
            self.show_sight(player_index)
            self.print_vpool(player_index)
            self.card_action(player_index,player_hand)
            self.is_game_over()
            # help to clean game
            if self.game_over.is_set():
                self.turn_start[(player_index+1)%self.number_of_players].is_set()
                self.turn_end[player_index].set()
                listen_thread.join()
                break
            message=(f"player {player_index} finished")
            self.broadcast(message)
            self.turn_end[player_index].set()
        
    # Listens and processes messages coming from the main process.
    def listen_to_main(self, player_index):
        while not self.game_over.is_set():
            if not self.to_child_queues[player_index].empty():
                message = self.to_child_queues[player_index].get()
                try:
                    self.unicast_info(message,player_index)
                except socket.error as e:
                    print(f"Error sending message to player {player_index}: {e}")

game = Game(number_of_players=2)
