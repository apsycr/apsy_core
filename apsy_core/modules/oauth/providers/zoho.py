from modules.oauth.provider_base import ProviderBase

class ZohoProvider(ProviderBase):

    def __init__(self):

        super().__init__("zoho")