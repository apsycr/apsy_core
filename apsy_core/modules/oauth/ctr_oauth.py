from modules.oauth.factory import OAuthFactory

class OAuth:

    def connect(self, provider, **kwargs):

        return OAuthFactory.create(provider).connect(**kwargs)

    def callback(self, provider, **kwargs):

        return OAuthFactory.create(provider).callback(**kwargs)

    def refresh_token(self, provider, **kwargs):

        return OAuthFactory.create(provider).refresh_token(**kwargs)

    def disconnect(self, provider, **kwargs):

        return OAuthFactory.create(provider).disconnect(**kwargs)

    def status(self, provider, **kwargs):

        return OAuthFactory.create(provider).status(**kwargs)