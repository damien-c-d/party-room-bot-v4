class LoadConfigException(Exception):

    def __init__(self, response):
        self.response = response


class InvalidWinnerAmount(Exception):
    def __init__(self, winner_str):
        self.message = f"Invalid winner amount specified: {winner_str}. Must be a whole number followed by a 'w'."


class InvalidRoleException(Exception):
    def __init__(self, role=None):
        if role is None:
            self.message = "That role does not exist or has not been mentioned properly."
        else:
            self.message = "That role cannot be used in a giveaway, please check the pinned message in #giveaways for" \
                           "available roles."


class InvalidTimeException(Exception):
    def __init__(self, time):
        self.message = f"Incorrect giveaway time specified. Here are the options:\n" \
                       f"#s = 1 second\n" \
                       f"#m = 1 minute\n" \
                       f"#h = 1 hour\n" \
                       f"#d = 1 day\n" \
                       f"#w = 1 week\n" \
                       f"#n = Untimed Giveaway (requires manual end)\n" \
                       f"*Replace # with a whole number*"


class NoActiveGiveawaysException(Exception):
    def __init__(self):
        self.message = f"No Active giveaways were found."


class WinnerPoolNotFoundException(Exception):
    def __init__(self, giveaway_id):
        self.message = f"No winner pool was found for giveaway with ID: {giveaway_id}"


class BlackListEmptyException(Exception):
    def __init__(self):
        self.message = f"Blacklist is currently empty."


class EmbedIsNoneException(Exception):
    def __init__(self, giveaway_id):
        self.message = f"Embed is None for giveaway with ID: {giveaway_id}"
