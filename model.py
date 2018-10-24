#!/usr/bin/env python3

from enum import Enum
import json
import numpy as np
import time
from collections import defaultdict, Counter
import string


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

        self.server_notifications = []
        self.last_winner = None
        self.winner_cards = None

    def add_player(self, player):
        self.players.append(player)

        self.server_notifications.append({'name': 'update_points'})
        notification = {
            'name': 'update_status',
        }
        self.server_notifications.append(notification)

    def remove_player(self, player):
        self.players.remove(player)

        notification = {
            'name': 'update_points',
        }
        self.server_notifications.append(notification)
        notification = {
            'name': 'update_status',
        }
        self.server_notifications.append(notification)

        notification = {
            'name': 'logout'
        }

        player.notifications.append(notification)

    def player_did_vote(self, player, option_id):
        if player not in self.players:
            return
        try:
            option = self.options[option_id]
        except Exception:
            return

        print('player' , player, 'voted', option_id, option)
        self.votes[player] = option

        self.server_notifications.append({'name': 'update_points'})

        if self.check_all_players_voted():
            self.go_to_play()
        else:
            notification = {
                'name': 'update_status',
            }
            self.server_notifications.append(notification)

    def player_did_select_card(self, player, card_id):
        if player not in self.players:
            return
        try:
            card = player.cards[card_id]
        except Exception:
            return

        self.player_selected_cards[player].append(card)

        self.server_notifications.append({'name': 'update_status'})
        self.server_notifications.append({'name': 'update_points'})

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

        notification = {
            'name': 'get_winner',
        }
        self.server_notifications.append(notification)
        notification = {
            'name': 'update_points',
        }
        self.server_notifications.append(notification)

    def go_to_play(self):
        self.check_winner()
        self.state = Game.State.PLAY
        self.options = []
        self.votes = {}

        self.current_black_card = Card.draw_cards(self.black, 1)[0]
        self.player_selected_cards = defaultdict(lambda: [])

        notification = {
            'name': 'go_to_play',
        }
        for p in self.players:
            p.notifications.append(notification)

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
            p.cards.extend(Card.draw_cards(self.white, len(selected_cards)))

        notification = {
            'name': 'go_to_vote',
        }
        for p in self.players:
            p.notifications.append(notification)

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

        self.cards = Card.draw_cards(game.white, 10)

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
