from modules.ws.services.validator import validar_identity
from modules.ws.repositories.ws_server_repo import upsert_ws_server
from modules.ws.repositories.ws_branch_repo import sync_sucursales
from modules.ws.handlers.handshake_app import handle_app_handshake
from modules.services.ws_settings import get_mirrors

async def handle_handshake(websocket, data):

    identity = data.get("payload")

    if not identity:
        raise Exception("Handshake sin payload")

    tipo = identity.get("tipo",'')
    
    if tipo == "app":
        await handle_app_handshake(
            websocket,
            identity
        )
        return

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
