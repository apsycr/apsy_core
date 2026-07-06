from modules.oauth.provider_base import ProviderBase

class MicrosoftProvider(ProviderBase):

    def __init__(self):

        super().__init__("microsoft")