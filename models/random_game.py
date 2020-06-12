from random import random

import discord

from models.exceptions import GameOver
from models.game import Game
from models.utils import create_embed, create_author_embed


class RandomGame(Game):

    def __init__(self, up_to):
        word_num = random.randint(0, 4)
        super().__init__(word_num, trivia=False)
        self.up_to = up_to
        self.guesses = 6
        self.num = random.randint(1, up_to)
        self.prize_points = up_to / 10
        self.name = "Random Number"
        self.incorrect_guesses = []
        self.last_message = None

    def guess(self, number):
        self.guesses -= 1
        if number == self.num:
            return True
        else:
            if self.guesses <= 0:
                raise GameOver("You ran out of guesses!", self.name, self.num)
            else:
                return False

    def random_embed(self):
        embed = create_author_embed("Random Number Game",
                                    "https://cdn.pixabay.com/photo/2014/04/03/10/11/question-mark-310100_960_720.png",
                                    discord.Color.blue(),
                                    False)
        embed.description = f"Guess a number between 1 and {self.up_to}"
        self.embed = embed
        return self.embed

    def add_incorrect_guess(self, x):
        self.incorrect_guesses.append(x)
        lower_or_higher = "Try something lower..." if self.num < x else "Try something higher..."
        if self.embed.fields == discord.Embed.Empty:
            self.embed.insert_field_at(0, name=f"Incorrect Guesses - {lower_or_higher}",
                                       value=" ".join(self.incorrect_guesses))
            self.embed.insert_field_at(1, name="Guesses Remaining:", value=str(self.guesses))
        else:
            self.embed.set_field_at(0, value=" ".join(x))
            self.embed.set_field_at(1, value=str(self.guesses))

    def game_over(self, message, reason, answer):
        self.embed.insert_field_at(2, name=message, value=f"{reason}\n\n"
                                                          f"The correct answer was: {answer}")
