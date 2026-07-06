from modules.config import load_config

class ProviderBase:

    def __init__(self, provider):

        self.provider = provider.lower()

        self.load_config()

    def load_config(self):

        cfg = load_config()

        providers = cfg.get("oauth", {}).get("providers", {})

        if self.provider not in providers:
            raise Exception(
                f"Proveedor '{self.provider}' no encontrado en configuracion"
            )

        settings = providers[self.provider]

        if not settings.get("enabled", False):
            raise Exception(
                f"Proveedor '{self.provider}' deshabilitado."
            )

        self.client_id = settings["client_id"]
        self.client_secret = settings["client_secret"]
        self.redirect_uri = settings["redirect_uri"]