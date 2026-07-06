from modules.oauth.providers.google import GoogleProvider
from modules.oauth.providers.microsoft import MicrosoftProvider
from modules.oauth.providers.zoho import ZohoProvider

class OAuthFactory:

    PROVIDERS = {

        "google": GoogleProvider,

        "microsoft": MicrosoftProvider,

        "zoho": ZohoProvider

    }

    @classmethod
    def create(cls, provider):

        provider = provider.lower()

        if provider not in cls.PROVIDERS:

            raise Exception(
                f"Proveedor no soportado: {provider}"
            )

        return cls.PROVIDERS[provider]()