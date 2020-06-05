from random import random

from models.exceptions import GameOver
from models.game import Game


class RandomGame(Game):

    def __init__(self, up_to):
        word_num = random.randint(0, 4)
        super().__init__(word_num, trivia=False)
        self.up_to = up_to
        self.guesses = 6
        self.num = random.randint(1, up_to)
        self.prize_points = up_to / 10
        self.name = "Random Number"

    def guess(self, number):
        self.guesses -= 1
        if number == self.num:
            return True
        else:
            if self.guesses <= 0:
                raise GameOver("You ran out of guesses!", self.name)
            else:
                return False


