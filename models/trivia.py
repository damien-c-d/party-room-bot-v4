from difflib import SequenceMatcher

from models.db_ops import DBOperation
from models.enums import GameTypes
from models.game import Game


class Trivia(Game):

    def __init__(self):
        word_num = None
        super().__init__(word_num, True)
        self.question, self.answers = self.get_trivia_question()

    def get_trivia_question(self):
        entry = self.choose_word()
        return entry['q'], entry['a']

    def guess(self, word, user_id):
        db = await DBOperation.new()
        try:
            for answer in self.answers:
                if SequenceMatcher(a=word, b=answer.lower()).ratio() > 0.94:
                    self.active = False
                    x = await db.get_game_score(user_id, GameTypes.trivia)
                    if x is None:
                        await db.add_new_game_score(user_id, GameTypes.trivia, 1)
                    else:
                        await db.update_game_score(user_id, x.get("trivia") + 1, GameTypes.trivia)
                    return True
                else:
                    return False
        finally:
            await db.close()



