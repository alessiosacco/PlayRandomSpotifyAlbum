import random
import string
from enum import Enum

import requests


class Album:

    def __init__(self, title: str, artists: [str], uri: str):
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


ALBUMS = {}


def get_album_list(access_token: string) -> [Album]:
    return ALBUMS.get(access_token, [])


def set_album_list(access_token: string, album_list: [Album]):
    ALBUMS[access_token] = album_list


def get_all_albums(access_token: str) -> [Album]:
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
            raise Exception("The album list could not be retrieved")
    return list(albums)


def process_albums(array_albums) -> [Album]:
    albums = []
    for album in array_albums:
        title = album['album']['name']
        artists = list(map(lambda artist: artist[
            'name'], album['album']['artists']))
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


def play_album(album: Album, access_token: str) -> PlayResponse:
    url = "https://api.spotify.com/v1/me/player/play"
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {'context_uri': album.uri}
    r = requests.put(url, headers=headers, json=data)
    if r.status_code == 204:
        return PlayResponse.SUCCESS
    elif r.status_code == 404:
        return PlayResponse.NO_DEVICE
    elif r.status_code == 403:
        return PlayResponse.NO_PREMIUM
    else:
        return PlayResponse.FAILURE
