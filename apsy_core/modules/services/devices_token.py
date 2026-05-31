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

            a.id,
            a.device_id,
            a.token,
            b.retorno as estado,

            a.idusuario,
            a.session_token,

            a.created_at,
            a.updated_at

        FROM ws_devices a

        INNER JOIN ws_estados_devices b
            on b.id = a.estado

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