from modules.db import ejecutar

def validate_device_token(
    request
):

    auth = request.headers.get(
        "Authorization",
        ""
    )

    if not auth.startswith(
        "Bearer "
    ):

        return {

            "ok": False,

            "msg": "Authorization requerido"

        }

    token = auth.replace(
        "Bearer ",
        ""
    ).strip()

    if not token:

        return {

            "ok": False,

            "msg": "Token requerido"

        }

    row = ejecutar(

        """

        SELECT

            id,
            device_id,
            token,
            estado,

            idusuario,
            session_token,

            created_at,
            updated_at

        FROM ws_devices

        WHERE token = %s

        LIMIT 1

        """,

        (token,),

        "one"

    )

    if not row:

        return {

            "ok": False,

            "msg": "Dispositivo no encontrado"

        }

    return {

        "ok": True,

        "device": row

    }