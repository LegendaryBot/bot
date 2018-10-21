from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session
from django.conf import settings
from django.core.cache import cache


__oauth_client = {}


def __get_battlenet_oauth(region: str):
    if region.upper() == 'US':
        client_id = settings.SOCIAL_AUTH_BATTLENET_OAUTH2_US_KEY
        client_secret = settings.SOCIAL_AUTH_BATTLENET_OAUTH2_US_SECRET
    else:
        client_id = settings.SOCIAL_AUTH_BATTLENET_OAUTH2_EU_KEY
        client_secret = settings.SOCIAL_AUTH_BATTLENET_OAUTH2_EU_SECRET
    client = BackendApplicationClient(client_id=client_id)
    token = cache.get(f'{region}_battlenet_token')
    if token:
        if region not in __oauth_client:
            __oauth_client[region] = OAuth2Session(client=client, token=token)
    else:
        __oauth_client[region] = OAuth2Session(client=client)
        token = __oauth_client[region].fetch_token(token_url=f"https://{region}.battle.net/oauth/token", client_id=client_id, client_secret=client_secret)
        cache.set(f'{region}_battlenet_token', token, 60*60*24)
    return __oauth_client[region]


def execute_battlenet_request(url, params=None):
    region = url.split(".")[0].split("//")[1]
    try:
        return __get_battlenet_oauth(region).get(url, params=params)
    except TokenExpiredError as e:
        cache.delete(f'{region}_battlenet_token')
        return __get_battlenet_oauth(region).get(url, params=params)
