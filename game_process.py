import threading
import queue
import random
import structure as s 

import copy
import multiprocessing

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

        # 创建和启动玩家线程
        self.player_processes = []
        for i in range(number_of_players):
            process = multiprocessing.Process(target=self.player_action, args=(i,))
            self.player_processes.append(process)
            process.start()
        self.init_barrier.wait()
        #index=0事件开始
        while not self.game_over.is_set():
            with self.lock:
                current_player = self.current_turn.value
            self.turn_start[current_player].set()  # 通知当前玩家开始回合

            # 等待当前玩家结束回合
            self.turn_end[current_player].wait()
            self.turn_end[current_player].clear()

            # 更新到下一个玩家
            with self.lock:
                self.current_turn.value = (self.current_turn.value + 1) % number_of_players
        #这里添加游戏内容
        # self.game_barrier.wait()
        # 等待所有线程完成
        for process in self.player_processes:
            process.join()

    def listen_to_son(self):
        while not self.game_over.is_set():
            while not self.to_main_queue.empty():
                message = self.to_main_queue.get()
                print("Main thread received:", message)
                if message.startswith("Information"):
                    # 解析消息以获取 player_dest
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
        for index, player_hand in enumerate(self.players_hands):
            if index != player_index:
                print(f"Player {index}'s cards: {player_hand}\n")
            else:
                print(f"You are {index} you cannot see your card\n")

    def print_vpool(self):
        print("Victory Pool:")
        for color, highest_number in self.victory_pool.items():
            print(f"  Color {color}: highest card number {highest_number}\n")
        total_cards = sum(self.victory_pool.values())
        total_score = total_cards
        print(f"Total score: {total_score}\n")

    def is_game_over(self):
        # case1: victory
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            print("Victory! All fireworks are completed.\n")
            self.game_over=True

        # case2: fuse token all used
        if self.fuse_tokens.count == 0:
            print("Game over! All fuse tokens are used.\n")
            self.game_over=True

        # case3: deck all used
        if not self.deck:
            print("Game over! No more cards in the deck.\n")
            self.game_over=True

        print("Game continues.\n")

    def card_action(self, player_index,player_hand):
        self.input_action()
        action_success=False
        while not action_success:
            if self.action == 'inform':
                action_success=self.inform(player_index)
            elif self.action == 'play':
                action_success=self.play_card(player_index,player_hand)
            elif self.action == 'discard':
                action_success=self.discard_card(player_index,player_hand)

    def input_action(self):
        input_sucess=False
        while not input_sucess:
            action_index=input("type your action index,1 for inform, 2 for play card,3 for discard\n")
            if action_index=='1':
                if self.information_tokens.count <= 0:
                    print("No information tokens left. Cannot give information.\n")
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
                print("wrong index!Try again.\n")

    def inform(self,player_index):
        # input and verify the info dest
        input_sucess=False
        while not input_sucess:
            player_dest=input("type player dest:")
            if player_dest.isdigit():
                player_dest=int(player_dest)
                if player_index==player_dest:
                    print("Can not use info token to yourself!\n")
                elif player_dest>=self.number_of_players or player_dest<0:
                    print("illegal index! The number you type must be limited into the number of player!\n")
                else:
                    input_sucess=True
            else:
                print("type an int!\n")
        # input and verify the action info
        input_sucess=False
        while not input_sucess:
            action_info=input("action of inform, type a color or a number of card\n")
            if action_info.isdigit() and int(action_info) in [1, 2, 3, 4, 5]:
                action_info = int(action_info)
                input_sucess = True
                input_type = 'number'
            elif action_info in self.colors:
                input_sucess = True
                input_type = 'color'
            else:
                print("illegal info!\n")
        # Execution
        with self.lock:
            self.information_tokens.count -= 1
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
            card_index=input("which card do you want to play, choose from 0 to 4:")
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                print("illegal info!\n")
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
            message=(f"Play:you added sucessfully{card_index} with {color} and {number} to victory pool!\n")
        else:
            self.fuse_tokens.count -=1
            self.played_cards.append(card_played)
            message=(f"Play:you droped your {card_index} with {color} and {number} and lose a fuse_token!\n")
        print(message)
        
        self.to_main_queue.put(message)
        '''with self.lock:
            player_hand[player_index]=self.deck.draw_card()
            self.players_hands[player_index]=player_hand'''
        player_hand[player_index]=self.deck.draw_card()
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
            self.turn_start[player_index].wait()  # 等待轮到自己的回合
            self.turn_start[player_index].clear()
            if self.game_over.is_set():
                break
            print(f"{player_index}'s turn!\n")
            self.show_sight(player_index)
            self.print_vpool()
            self.card_action(player_index,player_hand)
            self.is_game_over()
            self.current_turn = (self.current_turn + 1) % self.number_of_players
            print(f"player {player_index} finished")
            self.turn_end[player_index].set()
        #self.game_barrier.wait()
        listen_thread.join()

    def listen_to_main(self, player_index):
        while not self.game_over:
            if not self.to_child_queues[player_index].empty():
                message = self.to_child_queues[player_index].get()
                if message.startswith("Input"):
                    #logic
                    pass
                else:
                    print(f"Player {player_index} received message: {message}")

# 运行游戏
game = Game(number_of_players=2)
