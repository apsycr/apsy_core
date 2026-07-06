from datetime import datetime, timedelta

from modules.db import ejecutar_api


class OAuthDB:

    def save(
        self,
        idsucursal,
        oauth_uid,
        provider,
        correo,
        access_token,
        refresh_token,
        expires_in,
        scope,
        uso
    ):

        uso = (uso or "").upper()

        envio = uso in ("SEND", "BOTH")
        lectura = uso in ("READ", "BOTH")

        token_expira = datetime.now() + timedelta(
            seconds=int(expires_in or 0)
        )

        sql = """
            INSERT INTO oauth_sucursales(
                idsucursal,
                tipo,
                provider,
                correo,
                oauth_uid,
                access_token,
                refresh_token,
                token_expira,
                scope,
                estado,
                envio,
                lectura,
                fecha_creacion,
                fecha_actualizacion
            )
            VALUES(
                %s,
                'CLOUD',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                1,
                %s,
                %s,
                NOW(),
                NOW()
            )
            ON DUPLICATE KEY UPDATE
                provider            = VALUES(provider),
                correo              = VALUES(correo),
                oauth_uid           = VALUES(oauth_uid),
                access_token        = VALUES(access_token),
                refresh_token       = VALUES(refresh_token),
                token_expira        = VALUES(token_expira),
                scope               = VALUES(scope),
                estado              = 1,
                envio               = VALUES(envio),
                lectura             = VALUES(lectura),
                fecha_actualizacion = NOW()
        """

        ejecutar_api(
            sql,
            (
                idsucursal,
                provider,
                correo,
                oauth_uid,
                access_token,
                refresh_token,
                token_expira,
                scope,
                int(envio),
                int(lectura),
            ),
            "none"
        )

        return {
            "ok": True,
            "correo": correo,
            "provider": provider,
            "oauth_uid": oauth_uid
        }