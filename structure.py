class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def __repr__(self):
        return f"{self.color} {self.number}"

class PlayerHand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def play_card(self, index):
        return self.cards.pop(index)

    def __repr__(self):
        return f"PlayerHand({self.cards})"

class Token:
    def __init__(self, type, count):
        self.type = type  # 令牌的类型，例如 'information' 或 'fuse'
        self.count = count  # 令牌的数量

    def use(self):
        # 使用一个令牌
        if self.count > 0:
            self.count -= 1
            return True
        return False

    def replenish(self, amount=1):
        # 补充令牌
        self.count += amount

    def __repr__(self):
        return f"Token({self.type}, {self.count})"
