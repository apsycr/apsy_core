from modules.oauth.oauth_google import OAuthGoogle
from modules.oauth.oauth_microsoft import OAuthMicrosoft


class OAuth:

    def __init__(self):

        self.providers = {
            'google': OAuthGoogle(),
            'microsoft': OAuthMicrosoft()
        }

    def get_provider(self, provider: str):

        provider = provider.lower()

        if provider not in self.providers:
            raise Exception(
                f'Provider no soportado: {provider}'
            )

        return self.providers[provider]

    # =====================================
    # LOGIN
    # =====================================

    def login(
        self,
        provider: str,
        idsucursal: int = None
    ):

        oauth = self.get_provider(provider)

        return oauth.login(
            idsucursal=idsucursal
        )

    # =====================================
    # CALLBACK
    # =====================================

    def callback(
        self,
        provider: str,
        code: str,
        state: str = None
    ):

        oauth = self.get_provider(provider)

        return oauth.callback(
            code=code,
            state=state
        )

    # =====================================
    # STATUS
    # =====================================

    def status(
        self,
        provider: str,
        idsucursal: int
    ):

        oauth = self.get_provider(provider)

        return oauth.status(
            idsucursal=idsucursal
        )

    # =====================================
    # DISCONNECT
    # =====================================

    def disconnect(
        self,
        provider: str,
        idsucursal: int
    ):

        oauth = self.get_provider(provider)

        return oauth.disconnect(
            idsucursal=idsucursal
        )

    # =====================================
    # REFRESH TOKEN
    # =====================================

    def refresh_token(
        self,
        provider: str,
        idsucursal: int
    ):

        oauth = self.get_provider(provider)

        return oauth.refresh_token(
            idsucursal=idsucursal
        )