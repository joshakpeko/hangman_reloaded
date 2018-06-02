""" Hangman main entities classes: Player, Stats, Round. """

import sys
from collections import namedtuple
import utilities

class Player:
    """A player is represented by its id, name, and stats."""

    __session_idents = []

    def __init__(self, pname):
        player = utilities.get_player(pname)
        if player is None:
            self.ident  = self.__new_ident()
            self.name   = pname
            self.stats  = Stats(self)
        else:
            self.ident  = player.ident
            self.name   = player.name
            self.stats  = player.stats

    def __repr__(self):
        return self.name

    def __new_ident(self):
        """Set an identification number for a new player."""
        if len(self.__session_idents) == 0:
            new_ident = utilities.get_max_ident() + 1
        else:
            new_ident = max(self.__session_idents) + 1
        self.__session_idents.append(new_ident)
        return new_ident


class Round:
    """A new game round"""

    __lexicon = "french"    # default lexicon
    __max_attempts = 0xc    # smile :)
    __reward = 0b11         # smile again :)

    def __init__(self, player):
        if not isinstance(player, Player):
            raise ValueError("invalid player: %s" % player)
        self.suspended      = True  # signal to continue the round
        self.player         = player
        self.lexicon        = self.__lexicon
        self.__word         = ""    # the word to be found (hidden)
        self.__valid_chars  = []    # to handle non-ascii chars
        self.mask           = ""    # pattern revealing found letters
        self.symbols        = []    # list of non-alpha chars in word
        self.__attempts     = self.__max_attempts
        self.__reward       = self.__reward
        self.played_chars   = [set(), set()] # played chars and words

    @property
    def attempts(self):
        return self.__attempts

    @property
    def stopped(self):
        return self.suspended

    def start(self):
        """Initialize a new word to start playing."""

        if not self.suspended:
            return

        new_word = utilities.get_new_word(self.lexicon)
        if new_word == "":
            raise ValueError("no word found!")
        self.__word = new_word
        self.__valid_chars = utilities.decompose(new_word)
        self.mask, symbols = utilities.set_mask(new_word)
        self.symbols.extend(symbols)
        self.suspended = False

    def set_lexicon(self, new_lexicon):
        """Change session lexicon"""
        self.lexicon = new_lexicon

    def stop(self):
        """Cancel the ongoing round without updating user's stats."""

        self.__word = ""
        self.mask = ""
        self.__attempts = self.__max_attempts
        self.suspended = True

    def play(self, chars):
        """Play function processes a single character or a
        word played by the player, and update stats accordingly.
        chars can be a single character or a full word."""

        if self.suspended == True:
            return

        # reconstitute chars without in-word symbols
        alphas = "".join(c for c in chars if c not in self.symbols)

        # update mask to insert guessed characters
        if alphas.isalpha():
            self.__update_mask(chars)

        # add the user's proposal to played_chars list
        if len(chars) == 1:
            self.played_chars[0].add(chars)
        else:
            self.played_chars[1].add(chars)

        self.__attempts -= 1

        # if end of the round, update stats and end the round
        if self.mask == self.__word:            # success
            self.player.stats.update(self.__reward)
            utilities.save_to_db(self.player)   # update database
            self.stop()

        if self.__attempts == 0:                # failure
            self.stats.update(0b0)
            utilities.save_to_db(self.player)   # update database
            self.stop()

    def __update_mask(self, chars):

        """Update self.mask according to chars."""
        n = len(chars)
        new_mask = ""
        if n == 1:
            for i, pair in enumerate(self.__valid_chars):
                if chars in pair:
                    new_mask += self.__word[i]
                else:
                    new_mask += self.mask[i]
            self.mask = new_mask
        elif n > 1:
            if chars == self.__word:
                self.mask = self.__word


class Stats:
    """ Represents a player statistics """

    def __init__(self, player):
        if not isinstance(player, Player):
            raise ValueError("invalid player: %s" % player)
        self.player_name    = player.name
        self.__ngames       = 0     # number of played games
        self.__successes    = 0
        self.__failures     = 0
        self.__points       = 0
        self.__level        = 0     # from 5 defined level

    def get_stats(self):
        """Return a nametuple of all stats"""

        Stats = namedtuple("Stats", ["game_played", "successes",
            "failures", "points", "level"])

        return Stats(
                self.__ngames, self.__successes, 
                self.__failures, self.__points, self.__level)

    def update(self, reward):
        """Update player stats"""
        self.__ngames += 1
        self.__points += reward
        if reward > 0:
            self.__successes += 1
        else:
            self.__failures += 1
        self.__level = utilities.get_level(
                self.__ngames, self.__successes)
