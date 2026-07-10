from urllib.parse import urlencode
import requests
import jwt

from fastapi.responses import RedirectResponse

from modules.oauth.provider_base import ProviderBase
from modules.oauth.oauth_state import OAuthState


class ZohoProvider(ProviderBase):

    AUTH_URL = "https://accounts.zoho.com/oauth/v2/auth"
    TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
    USERINFO_URL = "https://mail.zoho.com/api/accounts"

    SCOPES = {
        "SEND": [
            "openid",
            "email",
            "profile",
            "ZohoMail.accounts.READ",
            "ZohoMail.messages.CREATE"
        ],
        "READ": [
            "openid",
            "email",
            "profile",
            "ZohoMail.messages.READ"
        ],
        "BOTH": [
            "openid",
            "email",
            "profile",
            "ZohoMail.messages.CREATE",
            "ZohoMail.messages.READ"
        ]
    }

    def __init__(self):

        super().__init__("zoho")

    def _url(self, url, dc="com"):

        return url.replace(".com", f".{dc}")

    # ==========================================
    # CONNECT
    # ==========================================

    def connect(
        self,
        uso="SEND",
        state=None
    ):

        context = OAuthState.decode(state)

        uso = context.get("uso", "SEND")

        dc = context.get("dc", "com")

        scopes = self.SCOPES.get(
            uso.upper(),
            self.SCOPES["SEND"]
        )

        params = {

            "client_id": self.client_id,

            "redirect_uri": self.redirect_uri,

            "response_type": "code",

            "scope": ",".join(scopes),

            "access_type": "offline",

            "prompt": "consent"

        }

        if state:
            params["state"] = state

        url = (
            self._url(self.AUTH_URL,dc) +
            "?" +
            urlencode(params)
        )

        return RedirectResponse(url)

    # ==========================================
    # CALLBACK
    # ==========================================

    def callback(
        self,
        code,
        state=None
    ):
        context = OAuthState.decode(state)

        dc = context.get("dc", "com")

        response = requests.post(

            self._url(self.TOKEN_URL,dc),

            data={

                "code": code,

                "client_id": self.client_id,

                "client_secret": self.client_secret,

                "redirect_uri": self.redirect_uri,

                "grant_type": "authorization_code"

            }

        )

        token = response.json()

        access_token = token.get("access_token")

        refresh_token = token.get("refresh_token")

        expires_in = token.get("expires_in")

        id_token = token.get("id_token")

        userinfo = jwt.decode(
            id_token,
            options={"verify_signature": False}
        )

        return {

            "ok": True,

            "provider": self.provider,

            "oauth_uid": userinfo.get("sub"),

            "correo": userinfo.get("email"),

            "nombre": userinfo.get("name"),

            "picture": userinfo.get("picture"),

            "access_token": access_token,

            "refresh_token": refresh_token,

            "expires_in": expires_in,

            "scope": token.get("scope"),

            "state": state

        }

    # ==========================================
    # REFRESH TOKEN
    # ==========================================

    def refresh_token(
        self,
        refresh_token
    ):

        response = requests.post(

            self.TOKEN_URL,

            data={

                "client_id": self.client_id,

                "client_secret": self.client_secret,

                "grant_type": "refresh_token",

                "refresh_token": refresh_token

            }

        )

        return response.json()

    # ==========================================
    # DISCONNECT
    # ==========================================

    def disconnect(self, **kwargs):

        return {
            "ok": True
        }