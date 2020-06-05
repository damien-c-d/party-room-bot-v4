import discord
from discord.ext import commands

from models.db_ops import DBOperation
from models.enums import GameTypes
from models.exceptions import GameOver
from models.random_game import RandomGame
from models.utils import channels, create_embed


class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.random_game: RandomGame = RandomGame(4)

    @commands.Cog.listener(name="on_message")
    async def games_message_handler(self, message):

        if message.author.bot or message.channel.id != channels["games"]:
            if self.random_game is not None and self.random_game.active and message.content.isdigit():
                db = await DBOperation.new()
                try:
                    if self.random_game.guess(int(message.content)):
                        self.random_game.active = False
                        x = await db.get_game_score(message.author.id, GameTypes.random)
                        if x is not None:
                            await db.update_game_score(x + self.random_game.prize_points)
                            await message.channel.send(create_embed(f"{self.random_game.name} Game Over",
                                                                    f"{message.author.display_name}"
                                                                    f" got the correct answer of: "
                                                                    f"{self.random_game.num}",
                                                                    discord.Color.red(),
                                                                    [f"{message.author.display_name}'s Random Score:",
                                                                     x + self.random_game.prize_points]))
                            self.random_game = None
                except GameOver as game_over:
                    self.random_game = None
                    return await message.channel.send(game_over.message)
                finally:
                    await db.close()


def setup(bot):
    bot.add_cog(Games(bot))
