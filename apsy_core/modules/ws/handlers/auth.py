from modules.services.mirror_manager import mirror_manager
from modules.db import ejecutar

async def handle_auth(websocket, data):

    token = data.get("token")

    if not token:
        raise Exception("Auth sin token")

    row = validar_token(token)

    if not row:
        raise Exception(
            "Token inválido"
        )

    if row["activo"] != 1:
        raise Exception(
            "Servidor inactivo"
        )

    mirrors = obtener_mirrors(
        row["id"]
    )

    if mirrors:

        await mirror_manager.register(
            row["id"],
            websocket
        )

    await websocket.send_json({
        "success": 1,
        "type": "auth_ok"
    })

def validar_token(token):

    return ejecutar("""

        SELECT
            id,
            token,
            activo
        FROM ws_servers
        WHERE token = %s
        LIMIT 1

    """, (token,), "one")

def obtener_mirrors(ws_server_id):

    return ejecutar("""

        SELECT
            id,
            alias
        FROM ws_sucursales
        WHERE ws_server_id = %s
        AND activo = 1
        AND alias <> ''

    """, (ws_server_id,), "all")