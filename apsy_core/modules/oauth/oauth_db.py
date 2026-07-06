from datetime import datetime,timedelta
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

        token_expira = datetime.now()+timedelta(
            seconds=expires_in
        )

        envio = 0
        lectura = 0

        if uso == "SEND":
            envio = 1

        elif uso == "READ":
            lectura = 1

        elif uso == "BOTH":
            envio = 1
            lectura = 1

        ejecutar_api(```
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
                lectura
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
                %s
            )
            ON DUPLICATE KEY UPDATE
                provider=VALUES(provider),
                access_token=VALUES(access_token),
                refresh_token=VALUES(refresh_token),
                token_expira=VALUES(token_expira),
                scope=VALUES(scope),
                estado=1,
                envio=VALUES(envio),
                lectura=VALUES(lectura)
        ```,
        (   
            idsucursal,
            provider,
            correo,
            oauth_uid,
            access_token,
            refresh_token,
            token_expira,
            scope,
            envio,
            lectura,
        ),
        'none')
