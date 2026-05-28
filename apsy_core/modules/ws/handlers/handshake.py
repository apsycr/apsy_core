from modules.ws.services.validator import validar_identity
from modules.ws.repositories.ws_server_repo import upsert_ws_server
from modules.ws.repositories.ws_branch_repo import sync_sucursales

async def handle_handshake(websocket, data):

    identity = data.get("payload")

    if not identity:
        raise Exception("Handshake sin payload")

    validar_identity(identity)

    ws_server = upsert_ws_server(identity)

    sync_sucursales(
        ws_server["id"],
        identity["payload"]
    )

    mirrors = get_mirrors(
        ws_server["id"]
    )

    await websocket.send_json({
        "type":"handshake_ok",
        "success":1,
        "ws_server_id": ws_server["id"],
        "token": ws_server["token"],
        "mirrors": mirrors
    })

def get_mirrors(ws_server_id):

    with get_db() as db:

        db.execute("""

            SELECT
                idsucursal,
                razon,
                alias

            FROM ws_sucursales

            WHERE ws_server_id = ?
            AND activo = 1

        """, (ws_server_id,))

        rows = db.fetchall()

        return [

            {
                "idsucursal": r[0],
                "razon": r[1],
                "alias": r[2]
            }

            for r in rows

        ]