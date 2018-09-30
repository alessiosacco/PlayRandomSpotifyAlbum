from flask import Flask, request, redirect, render_template, session

import authorization
import spotify_api

app = Flask(__name__)
app.secret_key = b'749f3b1f13331753c9a93f99733e978b'
BASE_REDIRECT_URI = 'http://localhost:5000/'

CLIENT_ID = "PLACEHOLDER"
CLIENT_SECRET = "PLACEHOLDER"

SCOPES = ['user-library-read',
          'user-read-playback-state',
          'user-modify-playback-state']


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/give-authorization', methods=['GET', 'POST'])
def give_authorization():
    authorization.set_permission_scopes(session, SCOPES)
    authorization.set_redirect_uri(session, BASE_REDIRECT_URI)
    return render_template('ask-authorization.html',
                           client_id=CLIENT_ID,
                           csrf_token=authorization.get_csrf_token(session),
                           scopes=" ".join(authorization.get_permission_scopes(session)),
                           redirect_uri=authorization.get_redirect_uri(session))


@app.route('/receive-authorization')
def receive_authorization():
    authorization_code = request.args.get('code', '')
    csrf_token = request.args.get('state', '')
    saved_token = authorization.get_csrf_token(session)
    if authorization_code == '' \
            or csrf_token == '' \
            or csrf_token != saved_token:
        return render_template('authorization-failure.html')
    else:
        authorization.set_authorization_code(session, authorization_code)
        authorization.Authorization(session, CLIENT_ID, CLIENT_SECRET).get_access_token()
        return redirect('/play-random')


@app.route('/play-random')
def play_random():
    access_token = authorization.get_access_token(session)
    is_expired = authorization.has_access_token_expired(session)
    if access_token == '':
        return redirect('/give-authorization')
    elif is_expired:
        authorization.Authorization(session, CLIENT_ID, CLIENT_SECRET).refresh_token()
        return redirect('/play-random')
    else:
        albums = spotify_api.get_album_list(access_token)
        if len(albums) == 0:
            albums = spotify_api.get_all_albums(access_token)
            spotify_api.set_album_list(access_token, albums)
        selected = spotify_api.select_random_album(albums)
        result = spotify_api.play_album(selected, access_token)
        if result == spotify_api.PlayResponse.SUCCESS:
            return render_template('play.html', success=True, album=str(selected))
        elif result == spotify_api.PlayResponse.NO_DEVICE:
            return render_template('play.html', success=False, reason="no device was found")
        elif result == spotify_api.PlayResponse.NO_PREMIUM:
            return render_template('play.html', success=False, reason="the account does not have premium")
        else:
            return render_template('play.html', success=False, reason="there was an error")
