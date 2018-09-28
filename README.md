# Introduction

Play a random album from the Spotify® library of the user. The user needs to have a currently active Spotify® Premium account and a currently active device capable of playing music.

# How to use

1. Install python 3 and pip

Instructions for Ubuntu 18.04

```
sudo apt update
sudo apt install python3
sudo apt install python3-pip
```

2. Install the `flask` and `requests` libraries

```
pip install requests
pip install Flask
```

3. Register as a developer to `https://developer.spotify.com/dashboard/`

4. Create a new application and get the client id and client secret

5. Substitute the values in `flask.sh`

6. Edit the settings of the application in the dashboard and add this redirect URI

```
http://localhost:5000/receive-authorization
```

7. Run `flask.sh`

8. Connect to `localhost:5000/` and follow the instructions

## Disclaimer

I am in no way affiliated to Spotify Technology SA nor do I own the Spotify® trademark.