import base64
import datetime
import random
import string

import requests


def set_redirect_uri(session, uri: str):
    session['redirect-uri'] = uri


def get_redirect_uri(session) -> str:
    return session['redirect-uri'] or ''


def __set_csrf_token(session):
    token = generate_token()
    session['csrf-token'] = token
    return token


def get_csrf_token(session) -> str:
    token = session['csrf-token'] or ''
    if token == '':
        token = __set_csrf_token(session)
    return token


def generate_token() -> str:
    candidates = string.ascii_uppercase + string.digits
    return ''.join(random.choice(candidates) for _ in range(32))


def set_authorization_code(session, auth_code: str):
    session['authorization-code'] = auth_code


def get_authorization_code(session) -> str:
    return session['authorization-code'] or ''


def set_permission_scopes(session, scopes: [str]):
    session['scopes'] = scopes


def get_permission_scopes(session):
    return session['scopes'] or []


def get_access_token(session) -> str:
    return session['access-token'] or ''


def set_access_token(session, access_token: str):
    session['access-token'] = access_token


def set_expiration_time(session, seconds: str):
    now = datetime.datetime.now()
    delta = datetime.timedelta(seconds=int(seconds))
    exp_time = now + delta
    session['expiration-time'] = exp_time


def has_access_token_expired(session) -> bool:
    now = datetime.datetime.now()
    return now > session['expiration-time']


def set_refresh_token(session, refresh_token: str):
    session['refresh-token'] = refresh_token


def get_refresh_token(session) -> str:
    return session['refresh-token'] or ''


class Authorization:

    def __init__(self, session, client_id: str, client_secret: str):
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret

    def get_access_token(self):
        url = "https://accounts.spotify.com/api/token"
        data = {
            'grant_type': "authorization_code",
            'code': get_authorization_code(self.session),
            'redirect_uri': get_redirect_uri(self.session) + 'receive-authorization',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        r = requests.post(url, data=data)
        if r.status_code == 200:
            obj = r.json()
            set_access_token(self.session, obj['access_token'])
            set_expiration_time(self.session, obj['expires_in'])
            set_refresh_token(self.session, obj['refresh_token'])
        else:
            print(r)
            raise Exception('The access token could not be retrieved')

    def refresh_token(self):
        url = "https://accounts.spotify.com/api/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': get_refresh_token(self.session),
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        r = requests.post(url, data=data)
        if r.status_code == 200:
            obj = r.json()
            set_access_token(self.session, obj['access_token'])
            set_expiration_time(self.session, obj['expires_in'])
        else:
            raise Exception("The access token could not be retrieved")
