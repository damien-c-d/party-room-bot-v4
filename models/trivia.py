from models.game import Game


class Trivia(Game):

    def __init__(self):
        word_num = None
        super().__init__(word_num, True)
        self.question = self.choose_word()
