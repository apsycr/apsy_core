from datetime import datetime, timedelta

from modules.db import ejecutar_api

class OAuthBase:

    def __init__(self):

        self.query = ejecutar_api

    # =====================================
    # ACCOUNT
    # =====================================

    def get_account(
        self,
        idsucursal,
        provider
    ):

        result = self.query(
            """
            SELECT
                *
            FROM oauth_sucursales
            WHERE idsucursal = %s
            AND provider = %s
            AND estado = 1
            LIMIT 1
            """,
            (
                idsucursal,
                provider
            ),
            "all"
        )

        if result:
            return result[0]

        return None

    # =====================================
    # SAVE ACCOUNT
    # =====================================

    def save_account(
        self,
        idsucursal,
        provider,
        correo,
        access_token,
        refresh_token,
        token_expira=None,
        oauth_uid=None,
        scope=None,
        tipo='LOCAL'
    ):

        account = self.get_account(
            idsucursal,
            provider
        )

        if account:

            self.query(
                """
                UPDATE oauth_sucursales
                SET
                    correo=%s,
                    oauth_uid=%s,
                    access_token=%s,
                    refresh_token=%s,
                    token_expira=%s,
                    scope=%s,
                    tipo=%s
                WHERE id=%s
                """,
                (
                    correo,
                    oauth_uid,
                    access_token,
                    refresh_token,
                    token_expira,
                    scope,
                    tipo,
                    account['id']
                ),
                "none"
            )

            return account['id']

        self.query(
            """
            INSERT INTO oauth_sucursales (
                idsucursal,
                provider,
                correo,
                oauth_uid,
                access_token,
                refresh_token,
                token_expira,
                scope,
                tipo
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            (
                idsucursal,
                provider,
                correo,
                oauth_uid,
                access_token,
                refresh_token,
                token_expira,
                scope,
                tipo
            ),
            "none"
        )

        account = self.get_account(
            idsucursal,
            provider
        )

        return account['id']

    # =====================================
    # STATUS
    # =====================================

    def status(
        self,
        idsucursal,
        provider
    ):

        account = self.get_account(
            idsucursal,
            provider
        )

        if not account:

            return {
                'connected': False
            }

        return {
            'connected': True,
            'correo': account['correo'],
            'provider': provider,
            'token_expira': account['token_expira']
        }

    # =====================================
    # DISCONNECT
    # =====================================

    def disconnect(
        self,
        idsucursal,
        provider
    ):

        self.query(
            """
            UPDATE oauth_sucursales
            SET
                estado = 0
            WHERE idsucursal = %s
            AND provider = %s
            """,
            (
                idsucursal,
                provider
            ),
            "none"
        )

        return {
            'ok': True
        }

    # =====================================
    # TOKEN
    # =====================================

    def token_expired(
        self,
        token_expira
    ):

        if not token_expira:
            return True

        if isinstance(
            token_expira,
            str
        ):

            token_expira = datetime.fromisoformat(
                token_expira
            )

        return datetime.now() >= token_expira

    # =====================================
    # UPDATE ACCESS TOKEN
    # =====================================

    def update_access_token(
        self,
        idsucursal,
        provider,
        access_token,
        expires_in=3600
    ):

        token_expira = (
            datetime.now()
            + timedelta(seconds=expires_in)
        )

        self.query(
            """
            UPDATE oauth_sucursales
            SET
                access_token=%s,
                token_expira=%s
            WHERE idsucursal=%s
            AND provider=%s
            """,
            (
                access_token,
                token_expira,
                idsucursal,
                provider
            ),
            "none"
        )

        return token_expira

    # =====================================
    # VALID TOKEN
    # =====================================

    def get_valid_token(
        self,
        idsucursal,
        provider
    ):

        account = self.get_account(
            idsucursal,
            provider
        )

        if not account:
            return None

        if not self.token_expired(
            account['token_expira']
        ):
            return account['access_token']

        return None