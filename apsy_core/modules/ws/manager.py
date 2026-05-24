import logging

from modules.ws.handlers.handshake import handle_handshake
from modules.ws.handlers.auth import handle_auth

logger = logging.getLogger("ws-cloud")

async def ws_connect(websocket, data):

    msg_type = data.get("type")

    logger.info(f"📩 WS MSG: {msg_type}")

    if msg_type == "handshake":

        await handle_handshake(websocket, data)

    elif msg_type == "auth":

        await handle_auth(websocket, data)

    else:

        await websocket.send_json({
            "success": 0,
            "message": "Tipo inválido"
        })