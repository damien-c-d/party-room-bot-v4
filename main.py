import discord
import os
from discord.ext import commands

from models.bot import Bot
from models.config import Config
from models.exceptions import LoadConfigException
from models.giveaway import Giveaway

if __name__ == "__main__":
    try:
        cfg = Config().data
        bot = Bot(cfg["token"], cfg["version"], cfg["bot_prefix"], cfg["music_prefix"], cfg["msg_req"],
                  cfg["msg_req_active"])

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                bot.load_extension(f"cogs.{filename[:-3]}")

        bot.run()

    except LoadConfigException as LCEx:
        print(f"Failed to load config.\r\nResponse: {LCEx.response}")
        wait = input()
    except Exception as Ex:
        print(Ex)
