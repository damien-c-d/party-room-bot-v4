from random import random

from models.game import Game


class Scrambled(Game):

    def __init__(self):
        word_num = random.randint(0, 4)
        super().__init__(word_num, False)
        self.unscrambled_word = self.choose_word()
        self.scrambled_word = self.get_scrambled_word(self.unscrambled_word)

    @staticmethod
    def shuffle_section(chars, section):
        shuffled = ""
        random.shuffle(chars)
        for char in section:
            if char == "-":
                shuffled += "-"
                chars.remove(char)
            else:
                choice = random.choice(chars)
                shuffled += choice
                chars.remove(choice)
        return shuffled

    @staticmethod
    def get_scrambled_word(word):
        chars = []
        scrambled = ""
        if ' ' in word:
            words = word.split(' ')
            for index, section in enumerate(words):
                chars += section
                if index != (len(words) - 1):
                    scrambled += f"{word.shuffle_section(chars, section)} "
                else:
                    scrambled += word.shuffle_section(chars, section)
        else:
            chars += word
            scrambled += word.shuffle_section(chars, word)
        return scrambled
