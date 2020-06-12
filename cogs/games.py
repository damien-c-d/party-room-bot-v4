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
        self.random_game = None

    # region Games Commands

    @commands.guild_only()
    @commands.command(name="random", aliases=["startrandom", "randomgame", "prandom"])
    async def random_game_command(self, ctx, upto: int = 10):
        if self.random_game is not None:
            if self.random_game.active:
                return await ctx.send("There is already a random number in progress. You can skip using !skiprandom")
        else:
            if upto < 10:
                return await ctx.send("The number specified must be at least 10.")
            self.random_game = RandomGame(upto)
            await ctx.send(embed=self.random_game.random_embed())

    # endregion Games Commands

    @commands.Cog.listener(name="on_message")
    async def games_message_handler(self, message):

        if message.author.bot or message.channel.id != channels["games"]:
            if self.random_game is not None and self.random_game.active and message.content.isdigit():
                if self.random_game.last_message is not None:
                    await self.random_game.last_message.delete()
                db = await DBOperation.new()
                try:
                    if self.random_game.guess(int(message.content)):
                        self.random_game.winner = message.author
                        self.random_game.active = False
                        x = await db.get_game_score(message.author.id, GameTypes.random)
                        if x is not None:
                            await db.update_game_score(x + self.random_game.prize_points)
                            raise GameOver(f"{message.author.display_name} got the correct answer!",
                                           self.random_game.name, self.random_game.num)

                    else:
                        self.random_game.add_incorrect_guess(int(message.content))
                        self.random_game.last_message = await message.channel.send(embed=self.random_game.embed)

                except GameOver as game_over:
                    self.random_game.game_over(game_over.message, game_over.reason, game_over.correct_answer)
                    await message.channel.send(embed=self.random_game.embed)
                finally:
                    self.random_game = None
                    await db.close()


def setup(bot):
    bot.add_cog(Games(bot))
