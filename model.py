#!/usr/bin/env python3

from enum import Enum
import json
import numpy as np
import time
from collections import defaultdict, Counter
import string
from uuid import uuid4


class Game:

    class State(Enum):
        PLAY=1
        VOTE=2
        #  WAIT=3

    def __init__(self):
        self.state = Game.State.PLAY

        white, black = Card.load_cards()
        white = [t.strip() for t in white if t.strip()]
        self.white = [Card(Card.Color.WHITE, t) for t in white]
        self.black = [Card(Card.Color.BLACK, t['text'], t['pick']) for t in black]
        self.players = []

        self.current_black_card = Card.draw_cards(self.black, 1)[0]

        self.player_selected_cards = defaultdict(lambda: [])

        self.options = []
        self.votes = {}

        self.notifications = {}

        self.server_notifications = []
        self.last_winner = None
        self.winner_cards = None

    def add_player(self, player):
        self.players.append(player)

        self.server_notifications.append(Notification('update_points', self))
        self.server_notifications.append(Notification('update_status', self))

    def remove_player(self, player):
        self.players.remove(player)

        self.server_notifications.append(Notification('update_points', self))
        self.server_notifications.append(Notification('update_status', self))

        player.notifications.append(Notification('logout', self, player))

    def player_did_vote(self, player, option_id):
        if player not in self.players:
            return
        try:
            option = self.options[option_id]
        except Exception:
            return

        print('player' , player, 'voted', option_id, option)
        self.votes[player] = option

        self.server_notifications.append(Notification('update_points', self))

        if self.check_all_players_voted():
            self.go_to_play()
        else:
            self.server_notifications.append(Notification('update_status', self))

    def player_did_clear_selection(self, player):
        if player not in self.players:
            return

        try:
            del self.player_selected_cards[player]
            self.server_notifications.append(Notification('update_status', self))
            self.server_notifications.append(Notification('update_points', self))
        except KeyError:
            pass


    def player_did_select_card(self, player, card_id):
        if player not in self.players:
            return
        try:
            card = player.cards[card_id]
        except Exception:
            return

        self.player_selected_cards[player].append(card)

        self.server_notifications.append(Notification('update_status', self))
        self.server_notifications.append(Notification('update_points', self))

        if self.check_all_players_played():
            self.go_to_vote()


    def check_all_players_played(self):
        for player in self.players:
            if (len(self.player_selected_cards.get(player, [])) !=
                    self.current_black_card.pick):
                return False
        return True

    def check_all_players_voted(self):
        for player in self.players:
            if player not in self.votes:
                return False
        return True

    def check_winner(self):
        counter = Counter(self.votes.values())
        print(counter)
        punctuations = list(counter.values())
        greatest_punctuation = max(punctuations)
        if punctuations.count(greatest_punctuation) > 1:
            self.last_winner = None
            self.winner_cards = None
        else:
            punctuations = counter.items()
            punctuations = sorted(punctuations,
                                  key=lambda x: x[1],
                                  reverse=True)
            winner = punctuations[0][0]
            winner.points += 1
            self.last_winner = winner
            self.winner_cards = self.player_selected_cards[winner]

        self.server_notifications.append(Notification('get_winner', self))
        self.server_notifications.append(Notification('update_points', self))

    def go_to_play(self):
        self.check_winner()
        self.state = Game.State.PLAY
        self.options = []
        self.votes = {}

        self.current_black_card = Card.draw_cards(self.black, 1)[0]
        self.player_selected_cards = defaultdict(lambda: [])

        for p in self.players:
            p.notifications.append(Notification('go_to_play', self, p))

    def go_to_vote(self):
        self.state = Game.State.VOTE
        options = list(self.player_selected_cards.keys())
        np.random.shuffle(options)
        self.options = options
        print('voting options', self.options)
        self.votes = {}
        for p in self.players:
            selected_cards = self.player_selected_cards[p]
            try:
                for card in selected_cards:
                    p.cards.remove(card)
            except ValueError:
                pass
            p.cards.extend(Card.draw_cards(self.free_white_cards(),
                                           len(selected_cards)))

        for p in self.players:
            p.notifications.append(Notification('go_to_vote', self, p))

    def change_cards(self, player):
        if player.points >= 1:
            player.cards = Card.draw_cards(self.free_white_cards(), 10)
            player.points -= 1
            player.notifications.append(Notification('update_info',
                                                     self,
                                                     player))
            self.server_notifications.append(Notification('update_points',
                                                          self))


    def free_white_cards(self):
        used_cards = set()
        for p in self.players:
            used_cards.update(p.cards)

        return [c for c in self.white if c not in used_cards]

    def player_has_played(self, player):
        if self.state == Game.State.PLAY:
            n_cards = len(self.player_selected_cards.get(player, []))
            return n_cards == self.current_black_card.pick
        elif self.state == Game.State.VOTE:
            return player in self.votes

class Player:
    def __init__(self, name, token, game):
        self.name = self.filter_name(name)
        self.token = token
        self.points = 1
        self.game = game

        self.cards = Card.draw_cards(game.free_white_cards(), 10)

        self.notifications = []

    def filter_name(self, name):
        name = ''.join(e for e in name if e.isalnum() or e == ' ')
        name = name[:10]
        return name

    def __repr__(self):
        return f'<Player {self.name}>'

class Card:
    class Color(Enum):
        WHITE = 1
        BLACK = 2

    def __init__(self, color, text, pick=None):
        self.color = color
        self.text = text
        self.last_used = 0
        self.pick = pick

    def __lt__(self, other):
        self.last_used < other.last_used

    def __repr__(self):
        return f'<Card {self.color} \"{self.text}\">'


    @staticmethod
    def draw_cards(deck, n):
        deck = deck[:]
        np.random.shuffle(deck)
        deck = sorted(deck, reverse=True)

        p = np.arange(len(deck)).astype('double')
        p = np.power(p, 2)
        p /= p.sum()

        selected_cards = np.random.choice(deck, size=n, replace=False, p=p)
        for card in selected_cards:
            card.last_used = time.time()

        np.random.shuffle(selected_cards)
        return list(selected_cards)

    @staticmethod
    def load_cards():
        with open('white.json') as fin:
            white = json.load(fin)
        with open('black.json') as fin:
            black = json.load(fin)

        return white, black

class Notification:
    def __init__(self, name, game, player=None, user_info=None):
        self.name = name
        self.user_info = user_info
        self.token = str(uuid4())
        self.active = True

        self.game = game
        self.player = player

        game.notifications[self.token] = self

    @property
    def serializable(self):
        return {
            'name': self.name,
            'user_info': self.user_info,
            'token': self.token,
        }
