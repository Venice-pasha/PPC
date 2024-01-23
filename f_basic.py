import random
import structure as s

class Game:
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
            for player_index in self.number_of_players:
                player_action(player_index, action, action_info)
                stop= is_game_over(self)
                if stop:
                    finish_game(self)
                    break


    def create_deck(self):
        if self.number_of_players==2:
            colors=['Red','Bleu']
        elif self.number_of_players==3:
            colors=['Red','Bleu','Green']
        numbers = [1, 2, 3, 4, 5]
        deck = [s.Card(color, number) for color in colors for number in numbers]
        random.shuffle(deck)
        return deck
    
    def create_token(self):
        information_tokens = s.Token('information', self.number_of_players + 3)
        fuse_tokens = s.Token('fuse', 3)
        return information_tokens, fuse_tokens

    def deal_cards(self):
        for player_hand in self.players_hands:
            for _ in range(5):
                player_hand.add_card(self.deck.pop())

    def create_victory_pool(self):
        return {color: 0 for color in self.colors}
    
    def is_game_over(self):
        """
        检查游戏是否结束。
        """
        # 条件1: 检查是否所有颜色的烟花都完成了（即每种颜色都达到了5）
        all_fireworks_completed = all(value == 5 for value in self.victory_pool.values())
        if all_fireworks_completed:
            print("Victory! All fireworks are completed.")
            return True

        # 条件2: 检查风险令牌是否用完
        if self.fuse_tokens.count == 0:
            print("Game over! All fuse tokens are used.")
            return True

        # 条件3: 检查牌堆是否为空
        # 这个条件疑似有问题
        if not self.deck:
            print("Game over! No more cards in the deck.")
            return True

        # 如果以上条件都不满足，游戏继续
        return False, "Game continues."
    
    def finish_game(self):
        pass

# a coder
class player_action:
    def __init__(self, player_index, action, action_info):
        """
        处理玩家的行动。

        :param player_index: 执行行动的玩家索引。
        :param action: 行动的类型，可以是 'inform'、'play' 或 'discard'。
        :param action_info: 执行行动所需的额外信息，比如要告知的信息或是要打出/丢弃的牌的索引。
        """
        if action == 'inform':
            self.inform(player_index, action_info)
        elif action == 'play':
            self.play_card(player_index, action_info)
        elif action == 'discard':
            self.discard_card(player_index, action_info)
        else:
            print("Unknown action.")

    def inform(self, player_index, information):
        # 执行告知行动的逻辑
        # 确保有足够的信息令牌
        if self.information_tokens > 0:
            self.information_tokens -= 1
            # 提供信息的逻辑...
        else:
            print("No information tokens left.")

    def play_card(self, player_index, card_index):
        # 执行打出卡牌的逻辑
        card = self.players_hands[player_index].play_card(card_index)
        # 检查卡牌是否能被成功打出的逻辑...
    
    def discard_card(self, player_index, card_index):
        # 执行丢弃卡牌的逻辑
        card = self.players_hands[player_index].play_card(card_index)
        # 回复一个信息令牌
        self.information_tokens += 1
        # 将卡牌加入到弃牌堆的逻辑...

#a coder
    # Add more methods for game actions here...
