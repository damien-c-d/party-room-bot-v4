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
            self.message = "That role cannot be used in this command."


class InvalidTimeException(Exception):
    def __init__(self, time):
        self.message = f"Invalid giveaway time specified. Time must be a number followed by either:\n" \
                       f"'s' for seconds, 'm' for minutes, 'h' for hours, 'd' for days, 'w' for weeks.\n" \
                       f"Or you can use '1n' for a non-timed giveaway."


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


class GameOver(Exception):
    def __init__(self, reason, name):
        self.message = f"{name} Game Over! {reason}"


class InvalidGameTypeException(Exception):
    def __init__(self, game_type):
        self.message = f"{game_type} is not a valid game type."
