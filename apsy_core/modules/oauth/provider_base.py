class ProviderBase:

    def __init__(self, provider):

        self.provider = provider

        self.load_config()

    def load_config(self):

        cfg = load_config()

        settings = cfg["oauth"]["providers"][self.provider]

        self.client_id = settings["client_id"]
        self.client_secret = settings["client_secret"]
        self.redirect_uri = settings["redirect_uri"]

    def connect(self, **kwargs):
        raise NotImplementedError

    def callback(self, **kwargs):
        raise NotImplementedError

    def refresh_token(self, **kwargs):
        raise NotImplementedError

    def disconnect(self, **kwargs):
        raise NotImplementedError