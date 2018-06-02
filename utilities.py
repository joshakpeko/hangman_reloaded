""" Utility functions for Hangman `entities` module """

import shelve
import random
import unicodedata


def get_max_ident():
    """Return the max id number attributed so far to a player.
    #Return -1 if there is none id attributed yet."""

    idents = []
    with shelve.open("data") as data:
        for player in data.values():
            idents.append(player.ident)
    if len(idents) == 0:
        return -1
    return max(idents)


def get_new_word(lexicon):
    """Randomly choose a word in from lexicon in the database
    and return it"""
    
    new_word = ""
    with shelve.open("words") as words:
        try:
            lex = words[lexicon]
        except KeyError:
            pass
        else:
            new_word = "".join(random.sample(lex, 1))
    return new_word


def decompose(word):
    """For each character in word, create a tuple containing
    the actual character and its ascii base character 
    (in case of unicode composition). Return a list of those
    tuples."""

    comp = []
    for c in word:
        bases = unicodedata.decomposition(c)
        if bases:
            first_hex = bases.split()[0]
            first_int = int(first_hex, 16)
            comp.append((c, chr(first_int)))
        else:
            comp.append((c,))
    return comp


def set_mask(word):
    """Return a tuple composed of a string where each alpha 
    character in word has been replaced with the 
    character '*', and a list of non-alpha characters in word."""

    mask = ""
    symbols = []
    for c in word:
        if c.isalpha():
            mask += "*"
        else:
            mask += c
            symbols.append(c)
    return (mask, symbols)


def save_to_db(player):
    """Save Player instance into database"""
    if player.__class__.__name__ != "Player":
        raise ValueError("player must be an instance of Player")
    with shelve.open("data") as data:
        data[player.name] = player
    return


def get_level(ngames, successes):
    """Determine and return an index between 0 and 4 representing
    the level of the player according to given stats. 4 being
    top-player rank."""

    level = 0
    average = successes / ngames

    scale_0 = [.25, .5, .75, 1]
    scale_1 = [.2, .4, .6, .9, 1]

    current_scale = scale_1 if ngames >= 10 else scale_0
    if  ngames < 3:     # play more than 3 rounds to get a new level
        return 0
    for i, s in enumerate(current_scale):
        if s >= average:
            return i


def get_player(player_name):
    """Return the player instance identified by pname if already
    registred. Return None otherwise."""

    with shelve.open("data") as data:
        if player_name in data.keys():
            return data[player_name]
        else:
            return None
