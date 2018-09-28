import datetime
import random
import string
import requests
import os
from enum import Enum

from flask import Flask, request, redirect, render_template, session

app = Flask(__name__)
app.secret_key = b'749f3b1f13331753c9a93f99733e978b'

client_ID = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']


class Album:

    def __init__(self, title: string, artists: [string], uri: string):
        self.title = title
        self.artists = artists
        self.uri = uri

    def __repr__(self):
        return "{} - {}".format(self.title, self.format_artists())

    def format_artists(self):
        s = ""
        for i, artist in enumerate(self.artists):
            if i < len(self.artists) - 2:
                s += "{}, ".format(artist)
            elif i == len(self.artists) - 2:
                s += "{} & ".format(artist)
            elif i == len(self.artists) - 1:
                s += "{}".format(artist)
        return s


def get_csrf_token() -> string:
    return session['csrf-token'] or ''


def set_csrf_token(token: string):
    session['csrf-token'] = token


def get_authorization_code() -> string:
    return session['authorization-code']


def set_authorization_code(code: string):
    session['authorization-code'] = code


def get_access_token() -> string:
    return session['access-code']


def set_access_token(code: string):
    session['access-code'] = code


def get_expiration_time() -> datetime.datetime:
    return session['expiration-time']


def set_expiration_time(remaining_seconds: string):
    exp_time = datetime.datetime.now() + datetime.timedelta(seconds=int(remaining_seconds))
    session['expiration-time'] = exp_time


@app.route("/")
def hello():
    return render_template('index.html')


@app.route('/give-authorization', methods=['GET', 'POST'])
def give_authorization():
    set_csrf_token(generate_token())
    scopes = ['user-library-read',
              'user-read-playback-state',
              'user-modify-playback-state']
    return render_template('ask-authorization.html',
                           client_id=client_ID,
                           csrf_token=get_csrf_token(),
                           scopes=" ".join(scopes))


@app.route('/receive-authorization')
def receive_authorization():
    authorization_code = request.args.get('code', '')
    csrf_token = request.args.get('state', '')
    if authorization_code == '' or csrf_token == '' or csrf_token != get_csrf_token():
        return render_template('authorization-failure.html')
    else:
        set_authorization_code(authorization_code)
        retrieve_access_token()
        return redirect('/play-random')


def generate_token() -> string:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))


def retrieve_access_token():
    auth_code = get_authorization_code()
    if auth_code != "":
        response = requests.post("https://accounts.spotify.com/api/token",
                                 data={'grant_type': 'authorization_code',
                                       'code': auth_code,
                                       'redirect_uri': 'http://localhost:5000/receive-authorization',
                                       'client_id': client_ID,
                                       'client_secret': client_secret})
        if response.status_code == 200:
            json = response.json()
            app.logger.debug(json['access_token'])
            set_access_token(json['access_token'])
            app.logger.debug(json['expires_in'])
            set_expiration_time(json['expires_in'])
            app.logger.debug(json)
        else:
            app.logger.debug(response)
        return "The access token has been received correctly"


@app.route('/play-random')
def play_random():
    access_token = get_access_token()
    if access_token != '' and datetime.datetime.now() < get_expiration_time():
        albums = get_all_albums(access_token)
        selected = select_random_album(albums)
        result = play_album(selected, access_token)
        if result == PlayResponse.SUCCESS:
            return render_template('play.html', success=True, album=str(selected))
        elif result == PlayResponse.NO_DEVICE:
            return render_template('play.html', success=False, reason="no device was found")
        elif result == PlayResponse.NO_PREMIUM:
            return render_template('play.html', success=False, reason="the account does not have premium")
        else:
            return render_template('play.html', success=False, reason="there was an error")
    elif access_token == "":
        return "The access token was not found"
    else:
        return "The access token has expired"


def get_all_albums(access_token: string) -> [Album]:
    url = "https://api.spotify.com/v1/me/albums"
    headers = {'Authorization': 'Bearer ' + access_token}
    finished = False
    albums = []
    while not finished:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            j = response.json()
            if j['next'] is not None:
                url = j['next']
            else:
                finished = True
            array_albums = j['items']
            albums = albums + process_albums(array_albums)
        else:
            app.logger.warning(
                "The request to get the albums was not successful")
            app.logger.debug(response)
    return list(albums)


def process_albums(array_albums) -> [Album]:
    albums = []
    for album in array_albums:
        app.logger.debug(album)
        title = album['album']['name']
        artists = list(map(lambda artist: artist['name'], album['album']['artists']))
        uri = album['album']['uri']
        albums.append(Album(title, artists, uri))
    return albums


def select_random_album(albums: [Album]) -> Album:
    n = len(albums)
    i = random.randrange(0, n)
    return albums[i]


class PlayResponse(Enum):
    SUCCESS = 0
    NO_DEVICE = 1
    NO_PREMIUM = 2
    FAILURE = 4


def play_album(album: Album, access_token: string) -> PlayResponse:
    url = "https://api.spotify.com/v1/me/player/play"
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {'context_uri': album.uri}
    app.logger.debug(url)
    app.logger.debug(headers)
    app.logger.debug(data)
    r = requests.put(url, headers=headers, json=data)
    app.logger.debug(str(r.request))
    if r.status_code == 204:
        return PlayResponse.SUCCESS
    elif r.status_code == 404:
        return PlayResponse.NO_DEVICE
    elif r.status_code == 403:
        return PlayResponse.NO_PREMIUM
    else:
        app.logger.debug(r)
        return PlayResponse.FAILURE
