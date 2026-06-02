from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from modules.ws.manager import ws_connect

logger = logging.getLogger("ws-cloud")

router = APIRouter(prefix="/ws")

@router.websocket("/connect")
async def websocket_entry(websocket: WebSocket):

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type")

            if msg_type == "action_response":

                await mirror_manager.handle_message(
                    data
                )

            elif msg_type in ("handshake", "auth"):

                await ws_connect(websocket, data)
            else:
                await websocket.send_json({
                    "success": 0,
                    "message": "Primer mensaje inválido"
                })

                await websocket.close(code=1008)
                return

    except WebSocketDisconnect:

        logger.warning("🔌 Cliente desconectado")

    except Exception as e:

        logger.exception("❌ WS ERROR")

        try:
            await websocket.send_json({
                "success": 0,
                "message": str(e)
            })
        except:
            pass

        await websocket.close()