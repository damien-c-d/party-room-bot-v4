from random import random

from models.game import Game


class Hangman(Game):
    def __init__(self, trivia):
        word_num = random.randint(0, 4)
        super().__init__(word_num, trivia)
        self.guesses = 6
        self.active = True
        self.solved = []
        self.wrong = []
        self.blank = []
        self.hang_word = self.get_word()

    def get_word(self):
        word = self.choose_word()
        self.solved += word
        for i in range(len(self.solved)):
            if self.solved[i] == " ":
                self.blank += " "
                self.blank += " "
            elif self.solved[i] == "-":
                self.blank += "-"
                self.blank += " "
            else:
                self.blank += "_"
                self.blank += " "
        return word
