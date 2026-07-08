from datetime import datetime, timedelta

from modules.db import ejecutar_api


class OAuthDB:

    def save(
        self,
        idtenant,
        oauth_uid,
        provider,
        correo,
        access_token,
        refresh_token,
        expires_in,
        scope,
        uso,
        dc
    ):

        token_expira = datetime.now() + timedelta(
            seconds=int(expires_in or 0)
        )

        sql = """
            INSERT INTO oauth_sucursales(
                idtenant,
                provider,
                oauth_uid,
                correo,
                access_token,
                refresh_token,
                token_expira,
                scope,
                estado,
                uso,
                fecha_creacion,
                fecha_actualizacion
            )
            VALUES(
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                1,
                %s,
                NOW(),
                NOW()
            )
            ON DUPLICATE KEY UPDATE
                provider            = VALUES(provider),
                oauth_uid           = VALUES(oauth_uid),
                correo              = VALUES(correo),
                access_token        = VALUES(access_token),
                refresh_token       = VALUES(refresh_token),
                token_expira        = VALUES(token_expira),
                scope               = VALUES(scope),
                estado              = 1,
                uso                 = VALUES(uso),
                fecha_actualizacion = NOW()
        """

        ejecutar_api(
            sql,
            (
                idtenant,
                provider,
                oauth_uid,
                correo,
                access_token,
                refresh_token,
                token_expira,
                scope,
                uso,
            ),
            "none"
        )

        return {
            "ok": True,
            "correo": correo,
            "provider": provider,
            "oauth_uid": oauth_uid
        }