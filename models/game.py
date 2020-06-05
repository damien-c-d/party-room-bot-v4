import json
from random import random


class Game(object):

    def __init__(self, word_num, trivia):
        if not trivia:
            with open("./res/words.json", 'r') as f:
                words = json.load(f)
                if word_num == 0:
                    self.category = "monsters"
                elif word_num == 1:
                    self.category = "locations"
                elif word_num == 2:
                    self.category = "food/potions"
                elif word_num == 3:
                    self.category = "weapons"
                elif word_num == 4:
                    self.category = "armour/equipment"
                self.words = words[self.category]
        elif trivia:
            with open("./res/trivia.json", 'r') as t:
                self.trivia_questions = json.load(t)
        self.active = False

    def shuffle_words(self):
        return random.shuffle(self.words)

    def start(self):
        self.active = True

    def choose_word(self):
        self.words.sort()
        for _ in range(4):
            random.shuffle(self.words)
        return random.choice(self.words)
