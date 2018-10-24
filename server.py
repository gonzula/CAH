#!/usr/bin/env python3

import json
from pprint import pprint
from flask import Flask
from flask import make_response, request, render_template, redirect
from flask import send_from_directory, send_file
from uuid import uuid4
import sys
import qrcode
import socket
from model import *
import io

app = Flask(__name__)


@app.route("/")
def home():
    return redirect('/play')

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('172.26.0.1', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

@app.route('/qrcode')
def get_qrcode():
    url = f'http://{get_ip()}:5000'
    img = qrcode.make(url)

    output_file = io.BytesIO()
    img.save(output_file, 'PNG')
    image_binary = output_file.getvalue()
    output_file.close()

    response = make_response(image_binary)
    response.headers.set('Content-Type', 'image/png')
    return response

@app.route("/server")
def server_home():
    return render_template('server.html', players=game.players)


@app.route('/all_points')
def get_points():
    players = sorted(game.players, key=lambda p: p.name.lower())
    points = [{'name': p.name, 'points': p.points, 'token': p.token, 'played': game.player_has_played(p)} for p in players]

    return json.dumps(points)

@app.route('/send_name', methods=['POST'])
def receive_name():
    name = request.form.get('name', f'Player {len(game.players)+1}')
    token = request.cookies.get('token')
    if token is not None:
        player = Player(name, token, game)
        game.add_player(player)
        sessions[token] = player

    return redirect('/play')

@app.route('/get_black_card')
def get_black_card():
    card = game.current_black_card
    pick = card.pick
    card = {
        'text': card.text,
    }
    if pick > 1:
        pick = f'Selecione {pick} cartas'
    else:
        pick = 'Selecione 1 carta'
    card['pick'] = pick
    return json.dumps(card)

@app.route('/get_status')
def get_status():
    card = game.current_black_card
    h1 = card.text

    if game.state == Game.State.PLAY:
        pick = card.pick
        if pick > 1:
            pick = f'Selecione {pick} cartas'
        else:
            pick = 'Selecione 1 carta'
        h2 = pick

        total = len(game.players)
        played = len(game.player_selected_cards)
        remaining = total - played
        if remaining > 1:
            h3 = f'Faltam {remaining} jogadores de {total} escolherem'
        else:
            h3 = f'Falta {remaining} jogador de {total} escolher'
    if game.state == Game.State.VOTE:
        h2 = 'Selecione a melhor'

        total = len(game.players)
        voted = len(game.votes)
        remaining = total - voted
        if remaining > 1:
            h3 = f'Faltam {remaining} jogadores de {total} votarem'
        else:
            h3 = f'Falta {remaining} jogador de {total} votar'


    status = {
        'h1': h1,
        'h2': h2,
        'h3': h3,
    }
    return json.dumps(status)


@app.route('/get_winner')
def get_winner():
    if game.last_winner:
        h2 = '\n'.join([c.text for c in game.winner_cards])
        h3 = f'O vencedor foi {game.last_winner.name}'
    else:
        h2 = 'Empate'
        h3 = None

    status = {
        'h2': h2,
        'h3': h3,
    }
    return json.dumps(status)


@app.route('/select_vote', methods=['POST'])
def select_vote():
    token = request.cookies.get('token')
    player = sessions.get(token)

    option = int(request.args.get('option'))
    game.player_did_vote(player, option)

    return json.dumps('ok')


@app.route('/vote')
def vote():
    token = request.cookies.get('token')
    player = sessions.get(token)
    if player is None or game.state == Game.State.PLAY:
        return redirect('/play')
    options = game.options
    options = [game.player_selected_cards[p] for p in options]
    options = [[card.text for card in option] for option in options]
    return render_template('vote.html', options=options)

@app.route('/play')
def play():
    token = request.cookies.get('token')
    player = sessions.get(token)
    if player is None:
        resp = make_response(render_template('player_ask_name.html'))
        resp.set_cookie('token', str(uuid4()))
        return resp

    if game.state == Game.State.VOTE:
        return redirect('/vote')

    pick = game.current_black_card.pick
    if pick > 1:
        pick_text = f'{pick} cartas'
    else:
        pick_text = '1 carta'

    return render_template('play.html',
                           pick_text=pick_text,
                           pick=game.current_black_card.pick,
                           player_name=player.name,
                           )

@app.route('/my_points')
def get_player_points():
    token = request.cookies.get('token')
    player = sessions.get(token)
    if player:
        return json.dumps(player.points)
    return json.dumps(-1)


@app.route('/my_cards')
def get_player_cards():
    token = request.cookies.get('token')
    player = sessions.get(token)
    cards = []
    if player:
        cards = [c.text for c in player.cards]

    return json.dumps(cards)

@app.route('/clear_selection', methods=['POST'])
def clear_selection():
    token = request.cookies.get('token')
    player = sessions.get(token)
    game.player_did_clear_selection(player)

    return json.dumps('ok')


@app.route('/select_card', methods=['POST'])
def player_select_card():
    token = request.cookies.get('token')
    player = sessions.get(token)
    cardIndex = int(request.args.get('index'))

    game.player_did_select_card(player, cardIndex)

    return json.dumps('ok')


@app.route('/remove_player', methods=['POST'])
def remove_player():
    token = request.args.get('token')
    player = sessions[token]
    game.remove_player(player)
    #  del sessions[token]

    return "ok"


@app.route('/received_notification', methods=['POST'])
def received_notification():
    token = request.args.get('token')
    note = game.notifications[token]
    note.active = False
    player = note.player

    if player:
        lst = player.notifications
    else:
        lst = game.server_notifications
    try:
        lst.remove(note)
    except ValueError:
        pass

    return json.dumps('ok')



@app.route('/server_notifications')
def get_server_notifications():
    notifications = game.server_notifications
    notifications = [n.serializable for n in notifications if n.active]

    return json.dumps(notifications)


@app.route('/player_notifications')
def get_player_notifications():
    token = request.cookies.get('token')
    player = sessions.get(token)
    try:
        notifications = player.notifications
        notifications = [n.serializable for n in notifications if n.active]
        return json.dumps(notifications)
    except Exception:
        return json.dumps([])


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

c = 0
game = Game()
sessions = {}

if __name__ == '__main__':
    app.run(host='0.0.0.0')
