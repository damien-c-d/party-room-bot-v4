from enum import Enum

from models.exceptions import InvalidGameTypeException


class GameTypes(Enum):
    random = 0
    hangman = 1
    unscramble = 2
    trivia = 3

    @staticmethod
    def get_type_name(game_type):
        if game_type == GameTypes.random:
            return "random"
        elif game_type == GameTypes.hangman:
            return "hangman"
        elif game_type == GameTypes.unscramble:
            return "scrambled"
        elif game_type == GameTypes.trivia:
            return "trivia"
        else:
            raise InvalidGameTypeException(game_type)
