import random

class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def __repr__(self):
        return f"{self.color} {self.number}"

class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def __repr__(self):
        return f"{self.color}-{self.number}"

# i dont think i've used it
# but i dare not delete it
class PlayerHand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def remove_card(self, index):
        if index < len(self.cards):
            return self.cards.pop(index)
        return None

    def replace_card(self, index, new_card):
        if index < len(self.cards):
            self.cards[index] = new_card

    def replace_random_card(self, new_card):
        if self.cards:
            random_index = random.randint(0, len(self.cards) - 1)
            self.replace_card(random_index, new_card)

    def is_empty(self):
        return len(self.cards) == 0

    def __repr__(self):
        return ', '.join(str(card) for card in self.cards)

# i dont think i've used it
# but i dare not delete it
class Token:
    def __init__(self, type, count):
        self.type = type
        self.count = count

    def use(self):
        if self.count > 0:
            self.count -= 1
            return True
        return False

    def replenish(self, amount=1):
        self.count += amount

    def __repr__(self):
        return f"Token({self.type}, {self.count})"

class Deck:
    def __init__(self, colors, numbers):
        self.cards = [Card(color, number) for color in colors for number in numbers]
        random.shuffle(self.cards)

    def draw_card(self):
        if self.cards:
            return self.cards.pop()
        return None

    def is_empty(self):
        return len(self.cards) == 0
