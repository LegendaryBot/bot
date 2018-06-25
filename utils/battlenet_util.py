import os

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


def get_battlenet_oauth(region: str):
    if region.upper() == 'US':
        client_id = os.getenv('US_KEY')
        client_secret = os.getenv('US_SECRET')
    else:
        client_id = os.getenv('EU_KEY')
        client_secret = os.getenv('EU_SECRET')
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.fetch_token(token_url="https://us.battle.net/oauth/token", client_id=client_id, client_secret=client_secret)
    return oauth
