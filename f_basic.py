import random
import copy
import structure as s

class Game:
    #level 1 programmme
    def __init__(self, number_of_players):
        #init game
        self.number_of_players = number_of_players
        self.players_hands = [s.PlayerHand() for _ in range(number_of_players)]
        self.played_cards = []
        self.deck = self.create_deck()
        self.information_tokens, self.fuse_tokens = self.create_tokens()
        self.deal_cards()
        self.victory_pool = self.create_victory_pool()
        #play game
        while True:
            for player_index in range(self.number_of_players):
                self.show_sight(player_index)
                self.print_vpool()
                self.player_action(player_index)
                stop,stop_message=self.is_game_over()
                print(stop_message)
                if stop:
                    self.print_vpool()
                    break

    #level 2 programme
    def create_deck(self):
        if self.number_of_players == 2:
            self.colors = ['Red', 'Bleu'] 
        if self.number_of_players == 3:
            self.colors = ['Red', 'Bleu', 'Green']
        numbers = [1]*3 + [2]*2 + [3]*2 + [4]*2 + [5]
        deck = [s.Card(color, number) for color in self.colors for number in numbers]
        random.shuffle(deck)
        return deck

    #level 2 programme
    def create_tokens(self):
        information_tokens = s.Token('information', self.number_of_players + 3)
        fuse_tokens = s.Token('fuse', 3)
        return information_tokens, fuse_tokens

    #level 2 programme
    def deal_cards(self):
        for player_hand in self.players_hands:
            for _ in range(5):
                player_hand.add_card(self.deck.pop())

    #level 2 programme
    def create_victory_pool(self):
        return {color: 0 for color in self.colors}
    
    #level 2 programme
    def show_sight(self,player_index):
        for index, player_hand in enumerate(self.players_hands):
            if index != player_index:
                print(f"Player {index}'s cards: {player_hand}\n")
            else:
                print(f"You are {index} you cannot see your card\n")
                
    #level 2 programme
    def is_game_over(self):
        # case1: victory
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            print("Victory! All fireworks are completed.\n")
            return True

        # case2: fuse token all used
        if self.fuse_tokens.count == 0:
            print("Game over! All fuse tokens are used.\n")
            return True

        # case3: deck all used
        if not self.deck:
            print("Game over! No more cards in the deck.\n")
            return True

        return False, "Game continues.\n"

    #level 2 programme
    def print_vpool(self):
        print("Victory Pool:")
        for color, highest_number in self.victory_pool.items():
            print(f"  Color {color}: highest card number {highest_number}")
        total_cards = sum(self.victory_pool.values())
        total_score = total_cards
        print(f"Total score: {total_score}")

    #level 2 programme, action of one player
    def player_action(self, player_index):
        self.input_action()
        action_success=False
        while not action_success:
            if self.action == 'inform':
                action_success=self.inform(player_index)
            elif self.action == 'play':
                action_success=self.play_card(player_index)
            elif self.action == 'discard':
                action_success=self.discard_card(player_index)

    #level 3 programme, subject of player action, check input of player
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
    
    #level 3 programme, 1st kind of action
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
        self.information_tokens.count -= 1
        player_hand=self.players_hands[player_dest]
        if (input_type == 'color'):
            qty,place=self.info_cardcolor(player_hand,action_info)
            message=(f"from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        elif (input_type == 'number'):
            qty,place=self.info_cardnumber(player_hand,action_info)
            message=(f"from {player_index}: Player {player_dest} has {action_info} card, quantity{qty}, place{place}.\n")
        print(message)
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
            card_index=input("which card do you want to play, choose from 0 to 4:")
            if card_index.isdigit() and int(card_index) in [1, 2, 3, 4, 0]:
                card_index = int(card_index)
                input_success = True
            else:
                print("illegal info!\n")
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
        print(message)
        (self.players_hands[player_index].cards)[card_index]=self.deck.pop()
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
        (self.players_hands[player_index].cards)[card_index]=self.deck.pop()
        print("a new card is in your hand, replace the card you've used.\n ")
        self.information_tokens += 1
        print("you've got a new info token.")
        return True


game = Game(number_of_players=2)
