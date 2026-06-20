class OAuthMicrosoft:

    def login(
        self,
        idsucursal=None
    ):

        return {
            'ok': True,
            'provider': 'microsoft',
            'action': 'login',
            'message': 'Pendiente implementar'
        }

    def callback(
        self,
        code,
        state=None
    ):

        return {
            'ok': True,
            'provider': 'microsoft',
            'action': 'callback',
            'message': 'Pendiente implementar'
        }

    def status(
        self,
        idsucursal
    ):

        return {
            'ok': True,
            'provider': 'microsoft',
            'connected': False
        }

    def disconnect(
        self,
        idsucursal
    ):

        return {
            'ok': True,
            'provider': 'microsoft',
            'message': 'Cuenta desconectada'
        }

    def refresh_token(
        self,
        idsucursal
    ):

        return {
            'ok': True,
            'provider': 'microsoft',
            'message': 'Refresh pendiente'
        }