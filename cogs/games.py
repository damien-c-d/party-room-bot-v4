from difflib import SequenceMatcher

from discord.ext import commands

from models.db_ops import DBOperation
from models.enums import GameTypes
from models.exceptions import GameOver
from models.hangman import Hangman
from models.random_game import RandomGame
from models.utils import channels


class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.random_game = None
        self.hangman_game = None

    # region Games Commands
    # region Start Games
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

    @commands.guild_only()
    @commands.command(name="hangman")
    async def hangman_game_command(self, ctx):
        if self.hangman_game is not None:
            if self.hangman_game.active:
                return await ctx.send("There is already a game of hangman in progress!")
        else:
            self.hangman_game = Hangman()
            await ctx.send(embed=self.hangman_game.hangman_embed())

    # endregion Start Games

    # region Game Guessing/Attempts
    @commands.guild_only()
    @commands.command(name="guess")
    async def guess_(self, ctx, *, guess):
        if self.hangman_game is not None:
            if self.hangman_game.active:
                guess = guess.lower()
                db = await DBOperation.new()
                try:
                    if SequenceMatcher(a=self.hangman_game.hang_word.lower(),
                                       b=guess()).ratio() > 0.90:
                        self.hangman_game.active = False
                        x = await db.get_game_score(ctx.author.id, GameTypes.hangman)
                        if x is not None:
                            await db.update_game_score(ctx.author.id, x + self.hangman_game.guesses, GameTypes.hangman)
                        else:
                            await db.add_new_game_score(ctx.author.id, self.hangman_game.guesses, GameTypes.hangman)
                        raise GameOver(f"{ctx.author.display_name} guessed the word!",
                                       self.hangman_game.name,
                                       self.hangman_game.hang_word)
                    elif guess in self.hangman_game.solved:
                        for index, letter in enumerate(self.hangman_game.solved):
                            if letter.lower() == guess:
                                self.hangman_game.blank[index + index] = guess
                        blanks = str("".join(self.hangman_game.blank))
                        self.hangman_game.add_letter()
                        await ctx.send(embed=self.hangman_game.hangman_embed)
                    else:
                        self.hangman_game.add_wrong_guess()
                except GameOver as game_over:
                    self.hangman_game.game_over()
                    await ctx.send(embed=self.hangman_game.hangman_embed)

                finally:
                    await db.close()
                    await ctx.message.delete()

    # endregion Game Guessing/Attempts

    # region Skip Games
    @commands.guild_only()
    @commands.command(name="skiprandom")
    async def skip_random_game(self, ctx):
        if self.random_game is not None:
            await self.random_game.last_message.delete()
            self.random_game.active = False
            self.random_game = None
        else:
            await ctx.send("There is no random number game currently active.")

    @commands.guild_only()
    @commands.command(name="skiphangman")
    async def skip_hangman_game(self, ctx):
        if self.hangman_game is not None:
            await self.hangman_game.last_message.delete()
            self.hangman_game.active = False
            self.hangman_game = None
        else:
            await ctx.send("There is no hangman game currently active.")

    # endregion Skip Games
    # endregion Games Commands

    # region Game Event Handlers
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
                            await db.update_game_score(message.author.id,
                                                       x + self.random_game.prize_points,
                                                       GameTypes.random)
                        else:
                            await db.add_new_game_score(message.author.id,
                                                        self.random_game.prize_points,
                                                        GameTypes.random)
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
    # endregion Game Event Handlers


def setup(bot):
    bot.add_cog(Games(bot))
