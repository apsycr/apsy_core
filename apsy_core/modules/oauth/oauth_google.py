from urllib.parse import urlencode
import requests

from modules.config import load_config
from modules.oauth.oauth_base import OAuthBase


class OAuthGoogle(OAuthBase):

    def __init__(self):

        super().__init__()

        self.provider = 'google'

        _config = load_config()
        oauth_cfg = _config['oauth']['providers']

        settings = oauth_cfg['google']

        self.client_id = settings.get(
            'client_id'
        )

        self.client_secret = settings.get(
            'client_secret'
        )

        self.redirect_uri = settings.get(
            'redirect_uri'
        )

        self.scopes = [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]

    # =====================================
    # LOGIN
    # =====================================

    def login(
        self,
        idsucursal=None
    ):

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = (
            'https://accounts.google.com/o/oauth2/v2/auth?'
            + urlencode(params)
        )

        return {
            'ok': True,
            'url': auth_url
        }

    # =====================================
    # CALLBACK
    # =====================================

    def callback(
        self,
        code,
        state=None
    ):

        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'grant_type': 'authorization_code',
                'code': code
            }
        )

        token_data = token_response.json()

        access_token = token_data.get(
            'access_token'
        )

        refresh_token = token_data.get(
            'refresh_token'
        )

        user_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={
                'Authorization':
                f'Bearer {access_token}'
            }
        )

        user_data = user_response.json()

        return {
            'ok': True,
            'provider': 'google',
            'correo': user_data.get('email'),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }

    # =====================================
    # STATUS
    # =====================================

    def status(
        self,
        idsucursal
    ):

        return super().status(
            idsucursal,
            self.provider
        )

    # =====================================
    # DISCONNECT
    # =====================================

    def disconnect(
        self,
        idsucursal
    ):

        return super().disconnect(
            idsucursal,
            self.provider
        )

    # =====================================
    # REFRESH TOKEN
    # =====================================

    def refresh_token(
        self,
        refresh_token
    ):

        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
        )

        return response.json()